"""
Voice/TTS module for HelloChusquis.

Ports OpenClaw's TTS architecture to Python:
- Multiple TTS providers with auto-detection
- Voice model catalog and selection
- Text normalization and directive parsing
- Speech-to-text (Whisper-based)
- Audio processing (format conversion, normalization, chunking)
- Caching and streaming support
"""

import abc
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Union,
)

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_CACHE_DIR = Path(tempfile.gettempdir()) / "hellochusquis" / "voice_cache"
DEFAULT_OUTPUT_FORMAT = "mp3"
SUPPORTED_AUDIO_FORMATS = {"mp3", "wav", "ogg", "flac", "m4a", "opus"}
MAX_CHUNK_CHARS = 4000  # safe limit before splitting text for synthesis
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 1.5

# ---------------------------------------------------------------------------
# Enums & dataclasses
# ---------------------------------------------------------------------------


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"
    OTHER = "other"


class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"
    M4A = "m4a"
    OPUS = "opus"


@dataclass
class VoiceInfo:
    """Metadata for a single voice."""

    voice_id: str
    name: str
    provider: str
    language: str = "en"
    gender: Gender = Gender.NEUTRAL
    preview_url: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    sample_rate: int = 22050
    description: str = ""

    def matches_language(self, lang_code: str) -> bool:
        return self.language.lower().startswith(lang_code.lower().split("-")[0])

    def matches_gender(self, gender: Gender) -> bool:
        return self.gender == gender


@dataclass
class TTSResult:
    """Result of a TTS synthesis call."""

    success: bool
    audio_path: Optional[str] = None
    audio_bytes: Optional[bytes] = None
    provider: str = ""
    voice_id: str = ""
    latency_ms: float = 0
    output_format: str = "mp3"
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class STTResult:
    """Result of a speech-to-text call."""

    success: bool
    text: str = ""
    language: str = ""
    provider: str = ""
    confidence: float = 0.0
    latency_ms: float = 0
    error: Optional[str] = None


@dataclass
class DirectiveOverrides:
    """Parsed TTS directive overrides from inline markup."""

    provider: Optional[str] = None
    voice: Optional[str] = None
    voice_id: Optional[str] = None
    speed: Optional[float] = None
    pitch: Optional[float] = None
    language: Optional[str] = None
    tts_text: Optional[str] = None
    provider_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class DirectiveParseResult:
    """Result of parsing TTS directives from text."""

    cleaned_text: str
    overrides: DirectiveOverrides = field(default_factory=DirectiveOverrides)
    has_directive: bool = False
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Abstract base: TTSProvider
# ---------------------------------------------------------------------------


class TTSProvider(abc.ABC):
    """Abstract base for all TTS providers."""

    provider_id: str = "base"
    supports_streaming: bool = False
    auto_select_order: int = 100

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any) -> None:
        self.api_key = api_key
        self.config = kwargs

    @abc.abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 1.0,
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> TTSResult:
        """Synthesize text to audio. Returns TTSResult."""

    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """Return available voices, optionally filtered by language."""
        return []

    def is_available(self) -> bool:
        """Check if this provider can be used right now."""
        return True

    def parse_directive_token(
        self, key: str, value: str, **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """Parse a provider-specific directive token. Returns overrides dict or None."""
        return None

    def _retry_request(
        self,
        func: Callable[..., Any],
        *args: Any,
        max_attempts: int = MAX_RETRY_ATTEMPTS,
        **kwargs: Any,
    ) -> Any:
        """Execute func with retries and exponential backoff."""
        last_exc: Optional[Exception] = None
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < max_attempts - 1:
                    time.sleep(RETRY_BACKOFF_BASE ** attempt)
        raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Provider: PiperTTS (local, free)
# ---------------------------------------------------------------------------


class PiperTTS(TTSProvider):
    """Local TTS using the Piper CLI (free, offline)."""

    provider_id = "piper"
    supports_streaming = False
    auto_select_order = 50

    # Piper model catalog (popular models)
    MODELS: Dict[str, Dict[str, Any]] = {
        "en_US-lessac-medium": {"language": "en", "gender": Gender.MALE},
        "en_US-libritts_r-medium": {"language": "en", "gender": Gender.FEMALE},
        "es_ES-sharvard-medium": {"language": "es", "gender": Gender.MALE},
        "es_ES-davefx-medium": {"language": "es", "gender": Gender.MALE},
        "fr_FR-siwis-medium": {"language": "fr", "gender": Gender.FEMALE},
        "de_DE-karlsson-low": {"language": "de", "gender": Gender.MALE},
        "ja_JP-kokoro-medium": {"language": "ja", "gender": Gender.FEMALE},
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._piper_bin = self._find_piper()

    def _find_piper(self) -> Optional[str]:
        """Locate the piper binary."""
        piper_path = shutil.which("piper")
        if piper_path:
            return piper_path
        # Check common install locations
        for candidate in [
            Path.home() / ".local" / "bin" / "piper",
            Path("/usr/local/bin/piper"),
            Path("/opt/homebrew/bin/piper"),
        ]:
            if candidate.exists():
                return str(candidate)
        return None

    def is_available(self) -> bool:
        return self._piper_bin is not None

    def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 1.0,
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> TTSResult:
        if not self._piper_bin:
            return TTSResult(success=False, error="Piper binary not found")

        # Resolve model
        model = self._resolve_model(voice_id, language)
        if not model:
            return TTSResult(
                success=False, error=f"No Piper model found for language={language}"
            )

        start = time.monotonic()
        try:
            with tempfile.NamedTemporaryFile(
                suffix=f".{output_format}", delete=False
            ) as tmp:
                tmp_path = tmp.name

            cmd = [
                self._piper_bin,
                "--model",
                model,
                "--output_file",
                tmp_path,
                "--length-scale",
                str(1.0 / speed),
            ]
            # Pipe text via stdin
            proc = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=60,
            )
            if proc.returncode != 0:
                return TTSResult(
                    success=False,
                    error=f"Piper failed: {proc.stderr.decode('utf-8', errors='replace')}",
                )

            audio_bytes = Path(tmp_path).read_bytes()
            latency = (time.monotonic() - start) * 1000
            return TTSResult(
                success=True,
                audio_path=tmp_path,
                audio_bytes=audio_bytes,
                provider=self.provider_id,
                voice_id=model,
                latency_ms=latency,
                output_format=output_format,
            )
        except subprocess.TimeoutExpired:
            return TTSResult(success=False, error="Piper synthesis timed out")
        except Exception as exc:
            return TTSResult(success=False, error=str(exc))

    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        voices = []
        for model_id, meta in self.MODELS.items():
            if language and not meta["language"].startswith(language.split("-")[0]):
                continue
            voices.append(
                VoiceInfo(
                    voice_id=model_id,
                    name=model_id,
                    provider=self.provider_id,
                    language=meta["language"],
                    gender=meta["gender"],
                )
            )
        return voices

    def _resolve_model(self, voice_id: Optional[str], language: str) -> Optional[str]:
        if voice_id and voice_id in self.MODELS:
            return voice_id
        # Find best match for language
        lang_prefix = language.split("-")[0].lower()
        for model_id, meta in self.MODELS.items():
            if meta["language"] == lang_prefix:
                return model_id
        return None


# ---------------------------------------------------------------------------
# Provider: OpenAI TTS
# ---------------------------------------------------------------------------


class OpenAITTS(TTSProvider):
    """OpenAI TTS API (paid)."""

    provider_id = "openai"
    supports_streaming = True
    auto_select_order = 20

    VOICES = {
        "alloy": Gender.NEUTRAL,
        "echo": Gender.MALE,
        "fable": Gender.MALE,
        "onyx": Gender.MALE,
        "nova": Gender.FEMALE,
        "shimmer": Gender.FEMALE,
    }

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(api_key=api_key or os.getenv("OPENAI_API_KEY"), **kwargs)
        self.base_url = "https://api.openai.com/v1"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 1.0,
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> TTSResult:
        if not self.api_key:
            return TTSResult(success=False, error="OpenAI API key not set")

        voice = voice_id or "alloy"
        if voice not in self.VOICES:
            voice = "alloy"

        # Map output format
        resp_format = output_format if output_format in {"mp3", "opus", "aac", "flac", "wav", "pcm"} else "mp3"

        start = time.monotonic()
        try:
            resp = self._retry_request(
                requests.post,
                f"{self.base_url}/audio/speech",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": kwargs.get("model", "tts-1"),
                    "input": text[:4096],
                    "voice": voice,
                    "response_format": resp_format,
                    "speed": max(0.25, min(4.0, speed)),
                },
                timeout=60,
            )
            resp.raise_for_status()

            latency = (time.monotonic() - start) * 1000
            ext = resp_format if resp_format != "pcm" else "wav"

            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name

            return TTSResult(
                success=True,
                audio_path=tmp_path,
                audio_bytes=resp.content,
                provider=self.provider_id,
                voice_id=voice,
                latency_ms=latency,
                output_format=ext,
            )
        except Exception as exc:
            return TTSResult(success=False, error=str(exc))

    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        return [
            VoiceInfo(
                voice_id=vid,
                name=vid,
                provider=self.provider_id,
                language="en",
                gender=gender,
            )
            for vid, gender in self.VOICES.items()
        ]

    def parse_directive_token(
        self, key: str, value: str, **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        if key in ("openai_voice", "openaivoice"):
            return {"voice": value}
        if key == "openai_model":
            return {"model": value}
        return None


# ---------------------------------------------------------------------------
# Provider: ElevenLabs TTS
# ---------------------------------------------------------------------------


class ElevenLabsTTS(TTSProvider):
    """ElevenLabs TTS API (paid, high quality)."""

    provider_id = "elevenlabs"
    supports_streaming = True
    auto_select_order = 10

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(
            api_key=api_key or os.getenv("ELEVENLABS_API_KEY"), **kwargs
        )
        self.base_url = "https://api.elevenlabs.io/v1"
        self._voice_cache: Optional[List[VoiceInfo]] = None

    def is_available(self) -> bool:
        return bool(self.api_key)

    def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 1.0,
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> TTSResult:
        if not self.api_key:
            return TTSResult(success=False, error="ElevenLabs API key not set")

        # Default to Rachel voice
        vid = voice_id or "21m00Tcm4TlvDq8ikWAM"

        start = time.monotonic()
        try:
            resp = self._retry_request(
                requests.post,
                f"{self.base_url}/text-to-speech/{vid}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": f"audio/{output_format}",
                },
                json={
                    "text": text,
                    "model_id": kwargs.get("model_id", "eleven_multilingual_v2"),
                    "voice_settings": {
                        "stability": kwargs.get("stability", 0.5),
                        "similarity_boost": kwargs.get("similarity_boost", 0.75),
                        "speed": max(0.25, min(4.0, speed)),
                    },
                },
                timeout=60,
            )
            resp.raise_for_status()

            latency = (time.monotonic() - start) * 1000
            with tempfile.NamedTemporaryFile(
                suffix=f".{output_format}", delete=False
            ) as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name

            return TTSResult(
                success=True,
                audio_path=tmp_path,
                audio_bytes=resp.content,
                provider=self.provider_id,
                voice_id=vid,
                latency_ms=latency,
                output_format=output_format,
            )
        except Exception as exc:
            return TTSResult(success=False, error=str(exc))

    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        if not self.api_key:
            return []
        if self._voice_cache is not None:
            voices = self._voice_cache
        else:
            try:
                resp = self._retry_request(
                    requests.get,
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key},
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                voices = []
                for v in data.get("voices", []):
                    labels = v.get("labels", {})
                    gender_str = labels.get("gender", "neutral").lower()
                    try:
                        gender = Gender(gender_str)
                    except ValueError:
                        gender = Gender.OTHER
                    voices.append(
                        VoiceInfo(
                            voice_id=v["voice_id"],
                            name=v.get("name", v["voice_id"]),
                            provider=self.provider_id,
                            language=labels.get("language", "en"),
                            gender=gender,
                            description=labels.get("description", ""),
                            labels=labels,
                        )
                    )
                self._voice_cache = voices
            except Exception:
                return []

        if language:
            voices = [v for v in voices if v.matches_language(language)]
        return voices

    def parse_directive_token(
        self, key: str, value: str, **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        if key in ("elevenlabs_voice", "elevenlabsvoice", "eleven_voice"):
            return {"voice_id": value}
        if key == "elevenlabs_stability":
            try:
                return {"stability": float(value)}
            except ValueError:
                return None
        if key == "elevenlabs_similarity":
            try:
                return {"similarity_boost": float(value)}
            except ValueError:
                return None
        return None


# ---------------------------------------------------------------------------
# Provider: Edge TTS (free, Microsoft)
# ---------------------------------------------------------------------------


class EdgeTTS(TTSProvider):
    """Microsoft Edge TTS (free, no API key required)."""

    provider_id = "edge"
    supports_streaming = True
    auto_select_order = 30

    # Popular Edge voices
    VOICE_MAP: Dict[str, Dict[str, str]] = {
        "en-US-AriaNeural": {"language": "en", "gender": "Female"},
        "en-US-GuyNeural": {"language": "en", "gender": "Male"},
        "en-US-JennyNeural": {"language": "en", "gender": "Female"},
        "es-ES-ElviraNeural": {"language": "es", "gender": "Female"},
        "es-ES-AlvaroNeural": {"language": "es", "gender": "Male"},
        "fr-FR-DeniseNeural": {"language": "fr", "gender": "Female"},
        "de-DE-KatjaNeural": {"language": "de", "gender": "Female"},
        "ja-JP-NanamiNeural": {"language": "ja", "gender": "Female"},
        "pt-BR-FranciscaNeural": {"language": "pt", "gender": "Female"},
        "zh-CN-XiaoxiaoNeural": {"language": "zh", "gender": "Female"},
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def is_available(self) -> bool:
        """Edge TTS is always available (free, no API key)."""
        return True

    def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 1.0,
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> TTSResult:
        voice = voice_id or self._resolve_voice(language)
        if not voice:
            return TTSResult(
                success=False, error=f"No Edge voice for language={language}"
            )

        # Speed/pitch to rate/pitch strings
        rate_pct = int((speed - 1.0) * 100)
        rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"
        pitch_pct = int((pitch - 1.0) * 100)
        pitch_str = f"+{pitch_pct}Hz" if pitch_pct >= 0 else f"{pitch_pct}Hz"

        start = time.monotonic()
        try:
            # Use edge-tts Python package if available, else CLI
            try:
                import edge_tts  # type: ignore

                return self._synth_with_lib(
                    text, voice, rate_str, pitch_str, output_format, start
                )
            except ImportError:
                return self._synth_with_cli(
                    text, voice, rate_str, pitch_str, output_format, start
                )
        except Exception as exc:
            return TTSResult(success=False, error=str(exc))

    def _synth_with_lib(
        self,
        text: str,
        voice: str,
        rate_str: str,
        pitch_str: str,
        output_format: str,
        start: float,
    ) -> TTSResult:
        import asyncio
        import edge_tts  # type: ignore

        with tempfile.NamedTemporaryFile(
            suffix=f".{output_format}", delete=False
        ) as tmp:
            tmp_path = tmp.name

        async def _run() -> None:
            communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
            await communicate.save(tmp_path)

        # Run async in sync context
        loop: Optional[asyncio.AbstractEventLoop] = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        if loop and loop.is_running():
            # We're inside an async context; run in new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _run())
                future.result(timeout=60)
        else:
            asyncio.run(_run())

        audio_bytes = Path(tmp_path).read_bytes()
        latency = (time.monotonic() - start) * 1000
        return TTSResult(
            success=True,
            audio_path=tmp_path,
            audio_bytes=audio_bytes,
            provider=self.provider_id,
            voice_id=voice,
            latency_ms=latency,
            output_format=output_format,
        )

    def _synth_with_cli(
        self,
        text: str,
        voice: str,
        rate_str: str,
        pitch_str: str,
        output_format: str,
        start: float,
    ) -> TTSResult:
        edge_bin = shutil.which("edge-tts")
        if not edge_bin:
            return TTSResult(
                success=False,
                error="edge-tts not found. Install: pip install edge-tts",
            )

        with tempfile.NamedTemporaryFile(
            suffix=f".{output_format}", delete=False
        ) as tmp:
            tmp_path = tmp.name

        cmd = [
            edge_bin,
            "--voice",
            voice,
            "--rate",
            rate_str,
            "--pitch",
            pitch_str,
            "--text",
            text,
            "--write-media",
            tmp_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=60)
        if proc.returncode != 0:
            return TTSResult(
                success=False,
                error=f"edge-tts failed: {proc.stderr.decode('utf-8', errors='replace')}",
            )

        audio_bytes = Path(tmp_path).read_bytes()
        latency = (time.monotonic() - start) * 1000
        return TTSResult(
            success=True,
            audio_path=tmp_path,
            audio_bytes=audio_bytes,
            provider=self.provider_id,
            voice_id=voice,
            latency_ms=latency,
            output_format=output_format,
        )

    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        voices = []
        for vid, meta in self.VOICE_MAP.items():
            if language and not meta["language"].startswith(language.split("-")[0]):
                continue
            try:
                gender = Gender(meta["gender"].lower())
            except ValueError:
                gender = Gender.OTHER
            voices.append(
                VoiceInfo(
                    voice_id=vid,
                    name=vid,
                    provider=self.provider_id,
                    language=meta["language"],
                    gender=gender,
                )
            )
        return voices

    def _resolve_voice(self, language: str) -> Optional[str]:
        lang_prefix = language.split("-")[0].lower()
        for vid, meta in self.VOICE_MAP.items():
            if meta["language"] == lang_prefix:
                return vid
        return None

    def parse_directive_token(
        self, key: str, value: str, **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        if key in ("edge_voice", "edgevoice"):
            return {"voice_id": value}
        return None


# ---------------------------------------------------------------------------
# Provider auto-detection
# ---------------------------------------------------------------------------


def _build_provider_registry() -> Dict[str, type]:
    """Build the provider class registry."""
    return {
        "piper": PiperTTS,
        "openai": OpenAITTS,
        "elevenlabs": ElevenLabsTTS,
        "edge": EdgeTTS,
    }


def detect_available_providers() -> Dict[str, bool]:
    """Return availability status for each registered provider."""
    registry = _build_provider_registry()
    result: Dict[str, bool] = {}
    for name, cls in registry.items():
        try:
            provider = cls()
            result[name] = provider.is_available()
        except Exception:
            result[name] = False
    return result


def get_provider(
    provider_id: str, api_key: Optional[str] = None, **kwargs: Any
) -> TTSProvider:
    """Instantiate a TTS provider by ID."""
    registry = _build_provider_registry()
    cls = registry.get(provider_id.lower())
    if cls is None:
        raise ValueError(f"Unknown TTS provider: {provider_id}")
    return cls(api_key=api_key, **kwargs)


def select_best_provider(
    preferred: Optional[str] = None,
    language: str = "en",
) -> TTSProvider:
    """Select the best available provider, optionally preferring one."""
    registry = _build_provider_registry()
    if preferred:
        provider = get_provider(preferred)
        if provider.is_available():
            return provider

    # Auto-select by priority (lower order = higher priority)
    candidates: List[Tuple[int, str, type]] = []
    for name, cls in registry.items():
        try:
            instance = cls()
            if instance.is_available():
                candidates.append((instance.auto_select_order, name, cls))
        except Exception:
            continue

    if not candidates:
        raise RuntimeError("No TTS providers available")

    candidates.sort(key=lambda c: c[0])
    _, best_name, best_cls = candidates[0]
    return best_cls()


# ---------------------------------------------------------------------------
# Text normalization (ported from OpenClaw speech-text.ts)
# ---------------------------------------------------------------------------

_CODE_HEAVY_THRESHOLD = 0.5
_FENCE_PATTERN = re.compile(r"(`{3,}|~{3,})", re.MULTILINE)
_INLINE_CODE_PATTERN = re.compile(r"`+[^`\n]+`+")
_HEADING_PATTERN = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
_BOLD_PATTERN = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_PATTERN = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_STRIKETHROUGH_PATTERN = re.compile(r"~~([^~]+)~~")
_BLOCKQUOTE_PATTERN = re.compile(r"^>\s?", re.MULTILINE)
_LIST_MARKER_PATTERN = re.compile(r"^[\s]*[-*+]\s+", re.MULTILINE)
_ORDERED_LIST_PATTERN = re.compile(r"^[\s]*\d+\.\s+", re.MULTILINE)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n[\s\S]*?\n---\s*\n")


def _count_fenced_code_chars(text: str) -> int:
    """Count characters inside fenced code blocks."""
    lines = text.split("\n")
    total = 0
    fence_re: Optional[re.Pattern[str]] = None
    body_lines: List[str] = []

    for line in lines:
        if fence_re is None:
            m = _FENCE_PATTERN.search(line.strip())
            if m:
                fence_re = re.compile(rf"^[`~]{{{len(m.group(1))},}}\s*$")
            continue
        if fence_re.match(line.strip()):
            total += len("\n".join(body_lines))
            fence_re = None
            body_lines = []
        else:
            body_lines.append(line)

    if fence_re is not None:
        total += len("\n".join(body_lines))
    return total


def is_code_heavy_text(text: str) -> bool:
    """Return True if text is mostly fenced code."""
    trimmed = text.strip()
    if not trimmed:
        return False
    return _count_fenced_code_chars(trimmed) / len(trimmed) >= _CODE_HEAVY_THRESHOLD


def strip_markdown_for_speech(text: str) -> str:
    """Strip markdown formatting for clean speech synthesis."""
    result = text
    # Remove frontmatter
    result = _FRONTMATTER_PATTERN.sub("", result)
    # Remove HTML tags
    result = _HTML_TAG_PATTERN.sub("", result)
    # Remove images entirely
    result = _IMAGE_PATTERN.sub("", result)
    # Links: keep label text
    result = _LINK_PATTERN.sub(r"\1", result)
    # Remove headings markers
    result = _HEADING_PATTERN.sub("", result)
    # Bold/italic markers
    result = _BOLD_PATTERN.sub(r"\1", result)
    result = _ITALIC_PATTERN.sub(r"\1", result)
    result = _STRIKETHROUGH_PATTERN.sub(r"\1", result)
    # Blockquote markers
    result = _BLOCKQUOTE_PATTERN.sub("", result)
    # List markers
    result = _LIST_MARKER_PATTERN.sub("", result)
    result = _ORDERED_LIST_PATTERN.sub("", result)
    # Inline code: keep content
    result = _INLINE_CODE_PATTERN.sub(lambda m: m.group().strip("`"), result)
    # Fenced code blocks: replace with placeholder
    code_block_re = re.compile(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)")
    result = code_block_re.sub("Code displayed on screen.", result)
    # Collapse multiple spaces/newlines
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = re.sub(r" {2,}", " ", result)
    return result.strip()


def normalize_speech_text(text: str) -> str:
    """Full normalization pipeline for TTS input."""
    trimmed = text.strip()
    if not trimmed:
        return ""
    if is_code_heavy_text(trimmed):
        return "I've put the detailed response on screen."
    return strip_markdown_for_speech(trimmed)


# ---------------------------------------------------------------------------
# VoiceDirective parser (ported from OpenClaw directives.ts)
# ---------------------------------------------------------------------------


class VoiceDirectiveParser:
    """Parse TTS directives from text using [[tts:...]] syntax.

    Supports:
    - [[tts:text]]...[[/tts:text]] — override spoken text
    - [[tts:provider=X]] — select provider
    - [[tts:speakervoice=X]] or [[tts:speaker_voice=X]] — select voice
    - [[tts:speakervoiceid=X]] — select voice ID
    - [[tts:text KEY=VALUE]] — inline directives
    - [[tts]]...[[/tts]] — plain block
    """

    # Patterns
    _BLOCK_TEXT_RE = re.compile(
        r"\[\[\s*tts\s*:\s*text\s*\]\]([\s\S]*?)\[\[\s*/\s*tts\s*:\s*text\s*\]\]",
        re.IGNORECASE,
    )
    _PLAIN_BLOCK_RE = re.compile(
        r"\[\[\s*tts\s*\]\]([\s\S]*?)\[\[\s*/\s*tts\s*\]\]", re.IGNORECASE
    )
    _DIRECTIVE_RE = re.compile(
        r"\[\[\s*tts\s*:\s*([^\]]+)\]\]", re.IGNORECASE
    )
    _BARE_TAG_RE = re.compile(r"\[\[\s*tts\s*\]\]", re.IGNORECASE)
    _CLOSING_RE = re.compile(
        r"\[\[\s*/\s*tts(?:\s*:\s*[^\]]*)?\]\]", re.IGNORECASE
    )

    # Markdown code ranges to avoid
    _CODE_RANGE_PATTERNS = [
        re.compile(r"```[\s\S]*?```"),
        re.compile(r"~~~[\s\S]*?~~~"),
        re.compile(r"^(?: {4}|\t).*(?:\n|$)", re.MULTILINE),
        re.compile(r"`+[^`\n]+`+"),
    ]

    def __init__(
        self,
        providers: Optional[List[TTSProvider]] = None,
        preferred_provider: Optional[str] = None,
    ) -> None:
        self.providers = providers or []
        self.preferred_provider = preferred_provider

    def _collect_code_ranges(self, text: str) -> List[Tuple[int, int]]:
        """Find ranges of markdown code to avoid replacing inside them."""
        ranges: List[Tuple[int, int]] = []
        for pattern in self._CODE_RANGE_PATTERNS:
            for m in pattern.finditer(text):
                ranges.append((m.start(), m.end()))
        ranges.sort(key=lambda r: r[0])
        return ranges

    def _is_inside_code(self, index: int, ranges: List[Tuple[int, int]]) -> bool:
        return any(start <= index < end for start, end in ranges)

    def _replace_outside_code(
        self,
        text: str,
        pattern: re.Pattern[str],
        replacer: Callable[[re.Match[str]], str],
    ) -> str:
        """Replace matches of pattern only if they fall outside code ranges."""
        code_ranges = self._collect_code_ranges(text)
        result: List[str] = []
        last_end = 0
        for m in pattern.finditer(text):
            if self._is_inside_code(m.start(), code_ranges):
                continue
            result.append(text[last_end : m.start()])
            result.append(replacer(m))
            last_end = m.end()
        result.append(text[last_end:])
        return "".join(result)

    def _find_provider(self, provider_id: str) -> Optional[TTSProvider]:
        """Find a provider by ID or alias."""
        normalized = provider_id.lower().strip()
        for p in self.providers:
            if p.provider_id == normalized:
                return p
        return None

    def _ordered_providers(self) -> List[TTSProvider]:
        """Return providers in auto-select order, with preferred first."""
        ordered = sorted(self.providers, key=lambda p: p.auto_select_order)
        if self.preferred_provider:
            preferred = self._find_provider(self.preferred_provider)
            if preferred:
                ordered = [preferred] + [p for p in ordered if p is not preferred]
        return ordered

    def parse(self, text: str) -> DirectiveParseResult:
        """Parse TTS directives from text, returning cleaned text and overrides."""
        if not text or not self._DIRECTIVE_RE.search(text):
            # Quick check: no tts directives
            if not self._BARE_TAG_RE.search(text) and not self._CLOSING_RE.search(text):
                return DirectiveParseResult(cleaned_text=text)

        overrides = DirectiveOverrides()
        warnings: List[str] = []
        cleaned = text

        def _handle_block_text(m: re.Match[str]) -> str:
            inner = m.group(1).strip()
            if inner and overrides.tts_text is None:
                overrides.tts_text = inner
            return ""

        def _handle_plain_block(m: re.Match[str]) -> str:
            inner = m.group(1).strip()
            if inner and overrides.tts_text is None:
                overrides.tts_text = inner
            return inner  # Keep visible text for plain blocks

        def _handle_directive(m: re.Match[str]) -> str:
            body = m.group(1).strip()
            tokens = body.split()
            for token in tokens:
                eq_idx = token.find("=")
                if eq_idx == -1:
                    continue
                key = token[:eq_idx].strip().lower()
                value = token[eq_idx + 1 :].strip()
                if not key or not value:
                    continue

                # Provider selection
                if key == "provider":
                    overrides.provider = value
                    continue

                # Generic speed/pitch/language
                if key == "speed":
                    try:
                        overrides.speed = float(value)
                    except ValueError:
                        pass
                    continue
                if key == "pitch":
                    try:
                        overrides.pitch = float(value)
                    except ValueError:
                        pass
                    continue
                if key == "language":
                    overrides.language = value
                    continue

                # Generic speaker voice
                if key in ("speakervoice", "speaker_voice"):
                    overrides.voice = value
                    overrides.voice_id = value
                    continue
                if key in ("speakervoiceid", "speaker_voice_id"):
                    overrides.voice_id = value
                    continue

                # Try provider-specific parsing
                handled = False
                for provider in self._ordered_providers():
                    parsed = provider.parse_directive_token(key, value)
                    if parsed:
                        overrides.provider_overrides.setdefault(
                            provider.provider_id, {}
                        ).update(parsed)
                        handled = True
                        break
                if not handled and overrides.provider:
                    warnings.append(
                        f"Unknown directive key '{key}' for provider '{overrides.provider}'"
                    )
            return ""

        def _handle_bare(_m: re.Match[str]) -> str:
            return ""

        def _handle_closing(_m: re.Match[str]) -> str:
            return ""

        cleaned = self._replace_outside_code(cleaned, self._BLOCK_TEXT_RE, _handle_block_text)
        cleaned = self._replace_outside_code(cleaned, self._PLAIN_BLOCK_RE, _handle_plain_block)
        cleaned = self._replace_outside_code(cleaned, self._DIRECTIVE_RE, _handle_directive)
        cleaned = self._replace_outside_code(cleaned, self._BARE_TAG_RE, _handle_bare)
        cleaned = self._replace_outside_code(cleaned, self._CLOSING_RE, _handle_closing)

        # Clean up extra whitespace
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        return DirectiveParseResult(
            cleaned_text=cleaned,
            overrides=overrides,
            has_directive=bool(
                overrides.tts_text or overrides.provider or overrides.voice
                or overrides.speed or overrides.pitch or overrides.language
                or overrides.provider_overrides
            ),
            warnings=warnings,
        )


# ---------------------------------------------------------------------------
# Stream text cleaner for directives
# ---------------------------------------------------------------------------


class TtsDirectiveStreamCleaner:
    """Incremental cleaner for stripping [[tts:...]] during streaming."""

    def __init__(self) -> None:
        self._pending = ""
        self._inside_hidden = False

    def push(self, text: str) -> str:
        """Process a chunk of streamed text, returning cleaned text."""
        inp = self._pending + text
        self._pending = ""
        output: List[str] = []
        idx = 0

        while idx < len(inp):
            tag_start = inp.find("[[", idx)
            if tag_start == -1:
                if not self._inside_hidden:
                    output.append(inp[idx:])
                break

            if not self._inside_hidden:
                output.append(inp[idx:tag_start])

            tag_end = inp.find("]]", tag_start + 2)
            if tag_end == -1:
                self._pending = inp[tag_start:]
                break

            tag_body = inp[tag_start + 2 : tag_end].strip().lower()
            if tag_body == "tts:text":
                self._inside_hidden = True
            elif tag_body == "/tts:text":
                self._inside_hidden = False
            elif (
                not self._inside_hidden
                and tag_body != "tts"
                and not tag_body.startswith("tts:")
                and not tag_body.startswith("/tts")
            ):
                output.append(inp[tag_start : tag_end + 2])

            idx = tag_end + 2

        return "".join(output)

    def flush(self) -> str:
        """Flush remaining buffered text."""
        tail = self._pending
        self._pending = ""
        return "" if self._inside_hidden else tail

    def has_buffered(self) -> bool:
        return bool(self._pending) or self._inside_hidden


# ---------------------------------------------------------------------------
# VoiceManager
# ---------------------------------------------------------------------------


class VoiceManager:
    """High-level voice management: selection, listing, caching, streaming."""

    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        preferred_provider: Optional[str] = None,
        default_language: str = "en",
    ) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.preferred_provider = preferred_provider
        self.default_language = default_language
        self._providers: Dict[str, TTSProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        """Initialize all available providers."""
        for name, cls in _build_provider_registry().items():
            try:
                provider = cls()
                if provider.is_available():
                    self._providers[name] = provider
            except Exception:
                continue

    @property
    def available_providers(self) -> List[str]:
        return list(self._providers.keys())

    def get_provider(self, provider_id: Optional[str] = None) -> TTSProvider:
        """Get a specific provider, or the best available one."""
        if provider_id and provider_id in self._providers:
            return self._providers[provider_id]
        return select_best_provider(self.preferred_provider, self.default_language)

    def list_voices(
        self,
        provider_id: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[VoiceInfo]:
        """List voices across providers or a specific one."""
        voices: List[VoiceInfo] = []
        providers = (
            [self._providers[provider_id]]
            if provider_id and provider_id in self._providers
            else list(self._providers.values())
        )
        for provider in providers:
            voices.extend(provider.list_voices(language))
        return voices

    def select_voice(
        self,
        language: str = "",
        gender: Optional[Gender] = None,
        provider_id: Optional[str] = None,
    ) -> Optional[VoiceInfo]:
        """Select best voice matching criteria."""
        lang = language or self.default_language
        voices = self.list_voices(provider_id, lang)
        if gender:
            voices = [v for v in voices if v.matches_gender(gender)]
        # Prefer higher auto_select_order provider
        return voices[0] if voices else None

    def _cache_key(
        self, text: str, voice_id: str, provider: str, fmt: str
    ) -> str:
        """Generate cache key from synthesis params."""
        h = hashlib.sha256()
        h.update(f"{provider}:{voice_id}:{fmt}:{text}".encode("utf-8"))
        return h.hexdigest()[:16]

    def _get_cached(self, key: str, fmt: str) -> Optional[str]:
        """Check for cached audio file."""
        cached = self.cache_dir / f"{key}.{fmt}"
        if cached.exists():
            return str(cached)
        return None

    def _put_cache(self, key: str, fmt: str, audio_bytes: bytes) -> str:
        """Store audio bytes in cache, return path."""
        out = self.cache_dir / f"{key}.{fmt}"
        out.write_bytes(audio_bytes)
        return str(out)

    def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "",
        speed: float = 1.0,
        pitch: float = 1.0,
        provider_id: Optional[str] = None,
        output_format: str = DEFAULT_OUTPUT_FORMAT,
        use_cache: bool = True,
        **kwargs: Any,
    ) -> TTSResult:
        """Synthesize text to speech with caching.

        Full pipeline: normalize -> parse directives -> chunk -> synthesize -> cache.
        """
        lang = language or self.default_language

        # Normalize text
        normalized = normalize_speech_text(text)
        if not normalized:
            return TTSResult(success=False, error="Empty text after normalization")

        # Parse directives
        providers = list(self._providers.values())
        parser = VoiceDirectiveParser(providers, self.preferred_provider)
        parse_result = parser.parse(normalized)

        # Apply overrides
        effective_text = parse_result.overrides.tts_text or parse_result.cleaned_text
        effective_provider = parse_result.overrides.provider or provider_id
        effective_voice = parse_result.overrides.voice_id or voice_id
        effective_speed = parse_result.overrides.speed or speed
        effective_pitch = parse_result.overrides.pitch or pitch

        # Check cache
        provider_obj = self.get_provider(effective_provider)
        cache_key = self._cache_key(
            effective_text, effective_voice or "", provider_obj.provider_id, output_format
        )
        if use_cache:
            cached_path = self._get_cached(cache_key, output_format)
            if cached_path:
                return TTSResult(
                    success=True,
                    audio_path=cached_path,
                    provider=provider_obj.provider_id,
                    voice_id=effective_voice or "",
                    output_format=output_format,
                    metadata={"cached": True},
                )

        # Chunk long text
        chunks = _chunk_text(effective_text, MAX_CHUNK_CHARS)
        if len(chunks) == 1:
            # Single chunk — direct synthesis
            result = provider_obj.synthesize(
                effective_text,
                voice_id=effective_voice,
                language=lang,
                speed=effective_speed,
                pitch=effective_pitch,
                output_format=output_format,
                **kwargs,
            )
            if result.success and result.audio_path and use_cache:
                result.audio_path = self._put_cache(
                    cache_key, output_format, result.audio_bytes or b""
                )
            return result

        # Multi-chunk synthesis
        chunk_results: List[TTSResult] = []
        for i, chunk in enumerate(chunks):
            chunk_key = f"{cache_key}_chunk{i}"
            if use_cache:
                cached = self._get_cached(chunk_key, output_format)
                if cached:
                    chunk_results.append(
                        TTSResult(
                            success=True,
                            audio_path=cached,
                            output_format=output_format,
                        )
                    )
                    continue

            r = provider_obj.synthesize(
                chunk,
                voice_id=effective_voice,
                language=lang,
                speed=effective_speed,
                pitch=effective_pitch,
                output_format=output_format,
                **kwargs,
            )
            if not r.success:
                return r
            if use_cache and r.audio_bytes:
                r.audio_path = self._put_cache(
                    chunk_key, output_format, r.audio_bytes
                )
            chunk_results.append(r)

        # Concatenate chunks
        combined = _concatenate_audio(
            [r.audio_path for r in chunk_results if r.audio_path], output_format
        )
        if combined is None:
            return TTSResult(success=False, error="Failed to concatenate audio chunks")

        if use_cache:
            combined = self._put_cache(cache_key, output_format, Path(combined).read_bytes())

        return TTSResult(
            success=True,
            audio_path=combined,
            provider=provider_obj.provider_id,
            voice_id=effective_voice or "",
            output_format=output_format,
            metadata={"chunks": len(chunks)},
        )

    def clear_cache(self) -> int:
        """Delete all cached audio files. Returns count deleted."""
        count = 0
        for f in self.cache_dir.iterdir():
            if f.is_file():
                f.unlink()
                count += 1
        return count


# ---------------------------------------------------------------------------
# SpeechToText
# ---------------------------------------------------------------------------


class SpeechToText:
    """Speech-to-text using Whisper (local CLI or API)."""

    def __init__(
        self,
        whisper_model: str = "base",
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
    ) -> None:
        self.whisper_model = whisper_model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base_url = api_base_url or "https://api.openai.com/v1"
        self._whisper_bin = shutil.which("whisper")

    def transcribe_file(
        self,
        audio_path: str,
        language: str = "en",
        use_api: bool = False,
        **kwargs: Any,
    ) -> STTResult:
        """Transcribe an audio file to text."""
        if use_api and self.api_key:
            return self._transcribe_api(audio_path, language, **kwargs)
        if self._whisper_bin:
            return self._transcribe_local(audio_path, language, **kwargs)
        if self.api_key:
            return self._transcribe_api(audio_path, language, **kwargs)
        return STTResult(
            success=False,
            error="No STT backend available. Install whisper CLI or set OPENAI_API_KEY.",
        )

    def transcribe_microphone(
        self,
        duration: int = 5,
        language: str = "en",
        **kwargs: Any,
    ) -> STTResult:
        """Record from microphone and transcribe."""
        try:
            import speech_recognition as sr  # type: ignore

            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=duration)

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio.get_wav_data())
                tmp_path = tmp.name

            return self._transcribe_local(tmp_path, language, **kwargs)
        except ImportError:
            return STTResult(
                success=False,
                error="speech_recognition not installed. Run: pip install SpeechRecognition",
            )
        except Exception as exc:
            return STTResult(success=False, error=str(exc))

    def _transcribe_local(
        self, audio_path: str, language: str, **kwargs: Any
    ) -> STTResult:
        """Transcribe using local whisper CLI."""
        if not self._whisper_bin:
            return STTResult(success=False, error="whisper CLI not found")

        start = time.monotonic()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cmd = [
                    self._whisper_bin,
                    audio_path,
                    "--model",
                    self.whisper_model,
                    "--language",
                    language,
                    "--output_format",
                    "json",
                    "--output_dir",
                    tmpdir,
                ]
                proc = subprocess.run(cmd, capture_output=True, timeout=300)
                if proc.returncode != 0:
                    return STTResult(
                        success=False,
                        error=f"Whisper failed: {proc.stderr.decode('utf-8', errors='replace')}",
                    )

                # Read JSON output
                json_files = list(Path(tmpdir).glob("*.json"))
                if not json_files:
                    return STTResult(success=False, error="No whisper output found")

                data = json.loads(json_files[0].read_text())
                text = data.get("text", "")
                lang = data.get("language", language)
                latency = (time.monotonic() - start) * 1000

                return STTResult(
                    success=True,
                    text=text,
                    language=lang,
                    provider="whisper-local",
                    latency_ms=latency,
                )
        except subprocess.TimeoutExpired:
            return STTResult(success=False, error="Whisper transcription timed out")
        except Exception as exc:
            return STTResult(success=False, error=str(exc))

    def _transcribe_api(
        self, audio_path: str, language: str, **kwargs: Any
    ) -> STTResult:
        """Transcribe using OpenAI Whisper API."""
        if not self.api_key:
            return STTResult(success=False, error="API key not set")

        start = time.monotonic()
        try:
            with open(audio_path, "rb") as f:
                resp = requests.post(
                    f"{self.api_base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": (os.path.basename(audio_path), f, "audio/wav")},
                    data={
                        "model": kwargs.get("model", "whisper-1"),
                        "language": language,
                    },
                    timeout=120,
                )
            resp.raise_for_status()
            data = resp.json()
            latency = (time.monotonic() - start) * 1000

            return STTResult(
                success=True,
                text=data.get("text", ""),
                language=language,
                provider="whisper-api",
                latency_ms=latency,
            )
        except Exception as exc:
            return STTResult(success=False, error=str(exc))


# ---------------------------------------------------------------------------
# AudioProcessor
# ---------------------------------------------------------------------------


class AudioProcessor:
    """Audio processing: format conversion, normalization, silence detection, chunking."""

    def __init__(self) -> None:
        self._ffmpeg = shutil.which("ffmpeg")
        self._ffprobe = shutil.which("ffprobe")

    def is_available(self) -> bool:
        return bool(self._ffmpeg)

    def convert_format(
        self,
        input_path: str,
        output_format: str = "wav",
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> Optional[str]:
        """Convert audio file to different format."""
        if not self._ffmpeg:
            return None

        out_path = Path(input_path).with_suffix(f".{output_format}")
        cmd = [
            self._ffmpeg,
            "-y",
            "-i", input_path,
            "-ar", str(sample_rate),
            "-ac", str(channels),
            "-f", output_format,
            str(out_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=60)
            return str(out_path) if out_path.exists() else None
        except Exception:
            return None

    def normalize(
        self,
        input_path: str,
        target_db: float = -20.0,
        output_format: str = "wav",
    ) -> Optional[str]:
        """Normalize audio volume using ffmpeg loudnorm."""
        if not self._ffmpeg:
            return None

        out_path = Path(input_path).with_suffix(f".norm.{output_format}")
        cmd = [
            self._ffmpeg,
            "-y",
            "-i", input_path,
            "-af", f"loudnorm=I={target_db}:TP=-1:LRA=11",
            "-ar", "16000",
            "-ac", "1",
            str(out_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=60)
            return str(out_path) if out_path.exists() else None
        except Exception:
            return None

    def detect_silence(
        self,
        input_path: str,
        threshold_db: float = -40.0,
        min_silence_ms: int = 500,
    ) -> List[Tuple[float, float]]:
        """Detect silence segments in audio. Returns list of (start, end) in seconds."""
        if not self._ffprobe or not self._ffmpeg:
            return []

        # Use ffmpeg silencedetect
        cmd = [
            self._ffmpeg,
            "-i", input_path,
            "-af", f"silencedetect=noise={threshold_db}dB:d={min_silence_ms / 1000}",
            "-f", "null",
            "-",
        ]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, timeout=60, text=True
            )
            silences: List[Tuple[float, float]] = []
            for line in proc.stderr.split("\n"):
                start_match = re.search(r"silence_start:\s*([\d.]+)", line)
                end_match = re.search(r"silence_end:\s*([\d.]+)", line)
                if start_match and end_match:
                    silences.append(
                        (float(start_match.group(1)), float(end_match.group(1)))
                    )
            return silences
        except Exception:
            return []

    def get_duration(self, input_path: str) -> float:
        """Get audio duration in seconds."""
        if not self._ffprobe:
            return 0.0
        cmd = [
            self._ffprobe,
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            input_path,
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(proc.stdout.strip())
        except Exception:
            return 0.0

    def chunk_audio(
        self, input_path: str, max_duration_s: float = 30.0
    ) -> List[str]:
        """Split audio into chunks by duration."""
        if not self._ffmpeg:
            return [input_path]

        duration = self.get_duration(input_path)
        if duration <= 0 or duration <= max_duration_s:
            return [input_path]

        chunks: List[str] = []
        start = 0.0
        idx = 0
        while start < duration:
            out_path = Path(input_path).with_suffix(f".chunk{idx}.wav")
            cmd = [
                self._ffmpeg,
                "-y",
                "-i", input_path,
                "-ss", str(start),
                "-t", str(max_duration_s),
                "-c", "copy",
                str(out_path),
            ]
            try:
                subprocess.run(cmd, capture_output=True, timeout=60)
                if out_path.exists():
                    chunks.append(str(out_path))
            except Exception:
                break
            start += max_duration_s
            idx += 1

        return chunks or [input_path]

    def concatenate(self, audio_paths: List[str], output_format: str = "wav") -> Optional[str]:
        """Concatenate multiple audio files."""
        if not audio_paths:
            return None
        if len(audio_paths) == 1:
            return audio_paths[0]
        if not self._ffmpeg:
            return None

        # Create concat list file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            for path in audio_paths:
                f.write(f"file '{path}'\n")
            list_path = f.name

        out_path = Path(audio_paths[0]).with_suffix(f".concat.{output_format}")
        cmd = [
            self._ffmpeg,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            str(out_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=120)
            return str(out_path) if out_path.exists() else None
        except Exception:
            return None
        finally:
            try:
                os.unlink(list_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _chunk_text(text: str, max_chars: int) -> List[str]:
    """Split text into chunks respecting sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        if current_len + len(sentence) + 1 > max_chars and current:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
        current.append(sentence)
        current_len += len(sentence) + 1

    if current:
        chunks.append(" ".join(current))

    return chunks


def _concatenate_audio(audio_paths: List[str], fmt: str) -> Optional[str]:
    """Concatenate audio files using AudioProcessor."""
    processor = AudioProcessor()
    return processor.concatenate(audio_paths, fmt)


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_global_manager: Optional[VoiceManager] = None
_global_stt: Optional[SpeechToText] = None


def get_voice_manager() -> VoiceManager:
    """Get or create the global VoiceManager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = VoiceManager()
    return _global_manager


def get_stt(
    whisper_model: str = "base", api_key: Optional[str] = None
) -> SpeechToText:
    """Get or create the global SpeechToText."""
    global _global_stt
    if _global_stt is None:
        _global_stt = SpeechToText(whisper_model=whisper_model, api_key=api_key)
    return _global_stt


def speak(
    text: str,
    voice_id: Optional[str] = None,
    language: str = "en",
    provider: Optional[str] = None,
    output_file: Optional[str] = None,
    **kwargs: Any,
) -> TTSResult:
    """Convenience: synthesize text and optionally save to file."""
    manager = get_voice_manager()
    result = manager.synthesize(
        text, voice_id=voice_id, language=language, provider_id=provider, **kwargs
    )
    if result.success and output_file and result.audio_path:
        shutil.copy2(result.audio_path, output_file)
        result.audio_path = output_file
    return result


def listen(
    audio_file: Optional[str] = None,
    duration: int = 5,
    language: str = "en",
) -> STTResult:
    """Convenience: transcribe audio file or microphone input."""
    stt = get_stt()
    if audio_file:
        return stt.transcribe_file(audio_file, language=language)
    return stt.transcribe_microphone(duration=duration, language=language)


def list_all_voices(language: Optional[str] = None) -> List[VoiceInfo]:
    """Convenience: list voices across all providers."""
    return get_voice_manager().list_voices(language=language)


def provider_status() -> Dict[str, bool]:
    """Convenience: check which TTS providers are available."""
    return detect_available_providers()
