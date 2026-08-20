"""
Media processing module for HelloChusquis.

Pure stdlib + subprocess (ffmpeg, pdftotext, ghostscript). No PIL/Pillow required.
Image operations use subprocess calls to ImageMagick (convert/identify) or ffmpeg.
PDF uses pdftotext + ghostscript. Audio uses ffmpeg/ffprobe.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Union

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_IMAGE_PIXELS = 25_000_000
_MAX_BASE64_ENCODED_CHARS = 16 * 1024 * 1024
_MAX_VISION_IMAGE_BYTES = 10 * 1024 * 1024
_IMAGE_REDUCE_QUALITY_STEPS = [85, 75, 65, 55, 45, 35]
_DEFAULT_QR_SCALE = 6
_DEFAULT_QR_MARGIN = 4
_MIN_QR_SCALE = 1
_MAX_QR_SCALE = 12
_MIN_QR_MARGIN = 0
_MAX_QR_MARGIN = 16
_VOICE_MESSAGE_EXTENSIONS = {".oga", ".ogg", ".opus", ".mp3", ".m4a"}
_VOICE_MESSAGE_MIMES = {
    "audio/ogg", "audio/opus", "audio/mpeg", "audio/mp3",
    "audio/mp4", "audio/x-m4a", "audio/m4a",
}

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _run(
    cmd: list[str],
    *,
    input_data: bytes | None = None,
    timeout: int = 60,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    """Run a subprocess, raise on failure, return CompletedProcess."""
    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            timeout=timeout,
            check=check,
            capture_output=capture,
        )
        return result
    except FileNotFoundError as exc:
        raise RuntimeError(f"Command not found: {cmd[0]}. Is it installed?") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Command timed out after {timeout}s: {cmd[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
        raise RuntimeError(f"Command failed ({cmd[0]}): {stderr[:500]}") from exc


def _which(name: str) -> str | None:
    """Find binary on PATH."""
    return shutil.which(name)


def _tmp_path(suffix: str = ".tmp") -> str:
    """Create a temp file path (caller responsible for cleanup)."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


def _detect_mime_from_bytes(data: bytes) -> str:
    """Detect MIME type from file header bytes (magic numbers)."""
    if len(data) < 2:
        return "application/octet-stream"
    # JPEG (needs 2 bytes)
    if data[:2] == b"\xff\xd8":
        return "image/jpeg"
    # BMP (needs 2 bytes)
    if data[:2] == b"BM":
        return "image/bmp"
    # MP3 ID3v2 tag (needs 3 bytes)
    if data[:3] == b"ID3":
        return "audio/mpeg"
    if len(data) < 4:
        return "application/octet-stream"
    # PNG
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    # GIF
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    # WebP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    # PDF
    if data[:5] == b"%PDF-":
        return "application/pdf"
    # MP3 (sync word)
    if data[:2] == b"\xff\xfb":
        return "audio/mpeg"
    # OGG/Opus
    if data[:4] == b"OggS":
        return "audio/ogg"
    # MP4/M4A
    if len(data) >= 12 and data[4:8] == b"ftyp":
        ftyp = data[8:12]
        if ftyp in (b"M4A ", b"isom", b"mp42", b"dash"):
            return "audio/mp4"
        return "video/mp4"
    # WAV
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "audio/wav"
    # FLAC
    if data[:4] == b"fLaC":
        return "audio/flac"
    # MKV/WebM
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "video/webm"
    # AVI
    if data[:4] == b"RIFF" and data[8:12] == b"AVI ":
        return "video/avi"
    return "application/octet-stream"


def _mime_to_ext(mime: str) -> str:
    """Map MIME type to file extension."""
    return {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "application/pdf": ".pdf",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/mp4": ".m4a",
        "audio/wav": ".wav",
        "audio/flac": ".flac",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/avi": ".avi",
    }.get(mime, ".bin")


def _require_bin(name: str, purpose: str = "") -> str:
    """Assert binary exists on PATH, return its path."""
    path = _which(name)
    if not path:
        msg = f"{name} not found on PATH"
        if purpose:
            msg += f" ({purpose})"
        raise RuntimeError(msg)
    return path


# ===================================================================
# ImageProcessor
# ===================================================================


@dataclass
class ImageMetadata:
    width: int = 0
    height: int = 0
    format: str = ""
    orientation: int = 0
    exif: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageResizeParams:
    max_side: int = 1024
    quality: int = 85
    format: str = "jpeg"
    enlarge: bool = False


class ImageProcessor:
    """    Image manipulation via ffmpeg/convert subprocess calls:
    resize, crop, rotate, flip, format conversion, thumbnails, EXIF extraction,
    base64 encode/decode, QR generation, and vision-model analysis.
    """

    def __init__(self, tmp_dir: str | None = None):
        self._tmp_dir = tmp_dir or tempfile.mkdtemp(prefix="hellochus-img-")
        self._bin_convert = _which("convert") or _which("magick")
        self._bin_ffprobe = _which("ffprobe")
        self._bin_ffmpeg = _which("ffmpeg")

    # ----------------------------------------------------------------
    # Metadata / probing
    # ----------------------------------------------------------------

    def _require_safe_pixel_count(self, path_or_bytes: Union[str, bytes]) -> None:
        """Reject images that would require excessive decoded-memory resources."""
        metadata = self.probe(path_or_bytes)
        pixels = metadata.width * metadata.height
        if pixels > _MAX_IMAGE_PIXELS:
            raise ValueError(
                f"Image exceeds pixel limit: {pixels} pixels (maximum {_MAX_IMAGE_PIXELS})"
            )

    def probe(self, path_or_bytes: Union[str, bytes]) -> ImageMetadata:
        """Read image dimensions, format, orientation, EXIF from header."""
        if isinstance(path_or_bytes, bytes):
            tmp = _tmp_path(".bin")
            try:
                with open(tmp, "wb") as f:
                    f.write(path_or_bytes)
                return self.probe(tmp)
            finally:
                os.unlink(tmp)

        path = str(path_or_bytes)
        meta = ImageMetadata()

        # Try ffprobe first
        if self._bin_ffprobe:
            try:
                result = _run(
                    [
                        self._bin_ffprobe,
                        "-v", "error",
                        "-select_streams", "v:0",
                        "-show_entries",
                        "stream=width,height,codec_name",
                        "-show_entries", "format=format_name,duration",
                        "-of", "json",
                        path,
                    ],
                    timeout=10,
                )
                data = json.loads(result.stdout)
                stream = (data.get("streams") or [{}])[0]
                meta.width = int(stream.get("width", 0))
                meta.height = int(stream.get("height", 0))
                meta.format = stream.get("codec_name", "")
                return meta
            except Exception:
                pass

        # Fallback: use identify (ImageMagick)
        if self._bin_convert:
            try:
                result = _run(
                    [self._bin_convert, "-format", "%w %h %m %[EXIF:Orientation]", path, "info:"],
                    timeout=10,
                )
                parts = result.stdout.decode(errors="replace").strip().split()
                if len(parts) >= 2:
                    meta.width = int(parts[0])
                    meta.height = int(parts[1])
                if len(parts) >= 3:
                    meta.format = parts[2]
                if len(parts) >= 4:
                    try:
                        meta.orientation = int(parts[3])
                    except ValueError:
                        pass
                return meta
            except Exception:
                pass

        # Last resort: parse header bytes
        with open(path, "rb") as f:
            header = f.read(32)
        meta.format = _detect_mime_from_bytes(header)
        return meta

    def probe_from_header(self, data: bytes) -> ImageMetadata:
        """Read image probe data from header bytes without full decode."""
        return self.probe(data)

    # ----------------------------------------------------------------
    # Resize
    # ----------------------------------------------------------------

    def resize(
        self,
        path_or_bytes: Union[str, bytes],
        *,
        max_side: int = 1024,
        quality: int = 85,
        output_format: str = "jpeg",
        enlarge: bool = False,
    ) -> bytes:
        """Resize image so longest side <= max_side, return encoded bytes."""
        self._require_safe_pixel_count(path_or_bytes)
        tmp_in = None
        tmp_out = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            ext = _mime_to_ext(f"image/{output_format}")
            tmp_out = _tmp_path(ext)

            size_flag = f"{max_side}x{max_side}"
            enlarge_flag = "" if enlarge else "\\>"

            if self._bin_convert:
                _run(
                    [
                        self._bin_convert,
                        in_path,
                        "-resize", f"{size_flag}{enlarge_flag}",
                        "-quality", str(quality),
                        tmp_out,
                    ],
                    timeout=30,
                )
            elif self._bin_ffmpeg:
                _run(
                    [
                        self._bin_ffmpeg, "-y",
                        "-i", in_path,
                        "-vf", f"scale='min({max_side},iw)':min'({max_side},ih)':force_original_aspect_ratio=decrease",
                        "-q:v", str(max(1, min(31, (100 - quality) * 31 // 100))),
                        tmp_out,
                    ],
                    timeout=30,
                )
            else:
                raise RuntimeError("No image processor available (install ImageMagick or ffmpeg)")

            with open(tmp_out, "rb") as f:
                return f.read()
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)
            if tmp_out and os.path.exists(tmp_out):
                os.unlink(tmp_out)

    def resize_to_jpeg(
        self,
        data: bytes,
        *,
        max_side: int = 1024,
        quality: int = 85,
        enlarge: bool = False,
    ) -> bytes:
        """Resize or encode image bytes as JPEG."""
        return self.resize(data, max_side=max_side, quality=quality, output_format="jpeg", enlarge=enlarge)

    # ----------------------------------------------------------------
    # Crop
    # ----------------------------------------------------------------

    def crop(
        self,
        path_or_bytes: Union[str, bytes],
        *,
        x: int = 0,
        y: int = 0,
        width: int = 100,
        height: int = 100,
    ) -> bytes:
        """Crop image to given rectangle, return encoded bytes."""
        self._require_safe_pixel_count(path_or_bytes)
        tmp_in = None
        tmp_out = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            tmp_out = _tmp_path(".jpg")
            geometry = f"{width}x{height}+{x}+{y}"

            if self._bin_convert:
                _run([self._bin_convert, in_path, "-crop", geometry, "+repage", tmp_out], timeout=30)
            elif self._bin_ffmpeg:
                _run(
                    [
                        self._bin_ffmpeg, "-y", "-i", in_path,
                        "-vf", f"crop={width}:{height}:{x}:{y}",
                        tmp_out,
                    ],
                    timeout=30,
                )
            else:
                raise RuntimeError("No image processor available")

            with open(tmp_out, "rb") as f:
                return f.read()
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)
            if tmp_out and os.path.exists(tmp_out):
                os.unlink(tmp_out)

    # ----------------------------------------------------------------
    # Rotate / flip
    # ----------------------------------------------------------------

    def rotate(self, path_or_bytes: Union[str, bytes], degrees: float) -> bytes:
        """Rotate image by given degrees, return encoded bytes."""
        self._require_safe_pixel_count(path_or_bytes)
        tmp_in = None
        tmp_out = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            tmp_out = _tmp_path(".jpg")

            if self._bin_convert:
                _run([self._bin_convert, in_path, "-rotate", str(degrees), tmp_out], timeout=30)
            elif self._bin_ffmpeg:
                _run(
                    [
                        self._bin_ffmpeg, "-y", "-i", in_path,
                        "-vf", f"rotate={degrees}*PI/180:fillcolor=black",
                        tmp_out,
                    ],
                    timeout=30,
                )
            else:
                raise RuntimeError("No image processor available")

            with open(tmp_out, "rb") as f:
                return f.read()
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)
            if tmp_out and os.path.exists(tmp_out):
                os.unlink(tmp_out)

    def flip(self, path_or_bytes: Union[str, bytes], horizontal: bool = True) -> bytes:
        """Flip image horizontally or vertically, return encoded bytes."""
        self._require_safe_pixel_count(path_or_bytes)
        tmp_in = None
        tmp_out = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            tmp_out = _tmp_path(".jpg")
            flag = "-flop" if horizontal else "-flip"

            if self._bin_convert:
                _run([self._bin_convert, in_path, flag, tmp_out], timeout=30)
            elif self._bin_ffmpeg:
                vf = "hflip" if horizontal else "vflip"
                _run(
                    [self._bin_ffmpeg, "-y", "-i", in_path, "-vf", vf, tmp_out],
                    timeout=30,
                )
            else:
                raise RuntimeError("No image processor available")

            with open(tmp_out, "rb") as f:
                return f.read()
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)
            if tmp_out and os.path.exists(tmp_out):
                os.unlink(tmp_out)

    # ----------------------------------------------------------------
    # Format conversion
    # ----------------------------------------------------------------

    def convert(self, path_or_bytes: Union[str, bytes], to_format: str) -> bytes:
        """Convert image to target format (png, jpeg, webp, gif)."""
        self._require_safe_pixel_count(path_or_bytes)
        tmp_in = None
        tmp_out = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            ext = _mime_to_ext(f"image/{to_format}")
            tmp_out = _tmp_path(ext)

            if self._bin_convert:
                _run([self._bin_convert, in_path, tmp_out], timeout=30)
            elif self._bin_ffmpeg:
                _run([self._bin_ffmpeg, "-y", "-i", in_path, tmp_out], timeout=30)
            else:
                raise RuntimeError("No image processor available")

            with open(tmp_out, "rb") as f:
                return f.read()
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)
            if tmp_out and os.path.exists(tmp_out):
                os.unlink(tmp_out)

    def to_jpeg(self, data: bytes, quality: int = 85) -> bytes:
        """Convert image to JPEG."""
        self._require_safe_pixel_count(data)
        tmp_in = _tmp_path(".bin")
        tmp_out = _tmp_path(".jpg")
        try:
            with open(tmp_in, "wb") as f:
                f.write(data)
            if self._bin_convert:
                _run([self._bin_convert, tmp_in, "-quality", str(quality), tmp_out], timeout=30)
            elif self._bin_ffmpeg:
                _run(
                    [self._bin_ffmpeg, "-y", "-i", tmp_in, "-q:v", str(max(1, (100 - quality) * 31 // 100)), tmp_out],
                    timeout=30,
                )
            else:
                raise RuntimeError("No image processor available")
            with open(tmp_out, "rb") as f:
                return f.read()
        finally:
            os.unlink(tmp_in)
            os.unlink(tmp_out)

    def to_png(self, data: bytes) -> bytes:
        """Convert image to PNG."""
        return self.convert(data, "png")

    def to_webp(self, data: bytes, quality: int = 80) -> bytes:
        """Convert image to WebP."""
        self._require_safe_pixel_count(data)
        tmp_in = _tmp_path(".bin")
        tmp_out = _tmp_path(".webp")
        try:
            with open(tmp_in, "wb") as f:
                f.write(data)
            if self._bin_convert:
                _run([self._bin_convert, tmp_in, "-quality", str(quality), tmp_out], timeout=30)
            elif self._bin_ffmpeg:
                _run(
                    [self._bin_ffmpeg, "-y", "-i", tmp_in, "-quality:v", str(quality), tmp_out],
                    timeout=30,
                )
            else:
                raise RuntimeError("No image processor available")
            with open(tmp_out, "rb") as f:
                return f.read()
        finally:
            os.unlink(tmp_in)
            os.unlink(tmp_out)

    # ----------------------------------------------------------------
    # Thumbnail generation
    # ----------------------------------------------------------------

    def thumbnail(
        self,
        path_or_bytes: Union[str, bytes],
        *,
        max_size: int = 128,
        quality: int = 75,
    ) -> bytes:
        """Generate a thumbnail image, return JPEG bytes."""
        self._require_safe_pixel_count(path_or_bytes)
        tmp_in = None
        tmp_out = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            tmp_out = _tmp_path(".jpg")

            if self._bin_convert:
                _run(
                    [
                        self._bin_convert,
                        in_path,
                        "-resize", f"{max_size}x{max_size}\\>",
                        "-quality", str(quality),
                        tmp_out,
                    ],
                    timeout=30,
                )
            elif self._bin_ffmpeg:
                _run(
                    [
                        self._bin_ffmpeg, "-y", "-i", in_path,
                        "-vf", f"scale='min({max_size},iw)':min'({max_size},ih)':force_original_aspect_ratio=decrease",
                        "-frames:v", "1",
                        "-q:v", str(max(1, (100 - quality) * 31 // 100)),
                        tmp_out,
                    ],
                    timeout=30,
                )
            else:
                raise RuntimeError("No image processor available")

            with open(tmp_out, "rb") as f:
                return f.read()
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)
            if tmp_out and os.path.exists(tmp_out):
                os.unlink(tmp_out)

    # ----------------------------------------------------------------
    # EXIF extraction
    # ----------------------------------------------------------------

    def extract_exif(self, path_or_bytes: Union[str, bytes]) -> dict[str, Any]:
        """Extract EXIF metadata from image. Returns dict of tag->value."""
        tmp_in = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            # Try ffprobe
            if self._bin_ffprobe:
                try:
                    result = _run(
                        [
                            self._bin_ffprobe,
                            "-v", "error",
                            "-show_entries", "format_tags",
                            "-show_entries", "stream_tags",
                            "-of", "json",
                            in_path,
                        ],
                        timeout=10,
                    )
                    data = json.loads(result.stdout)
                    tags: dict[str, Any] = {}
                    fmt_tags = data.get("format", {}).get("tags", {})
                    for stream in data.get("streams", []):
                        for k, v in stream.get("tags", {}).items():
                            tags[k] = v
                    tags.update(fmt_tags)
                    return tags
                except Exception:
                    pass

            # Fallback: use exiftool if available
            bin_exiftool = _which("exiftool")
            if bin_exiftool:
                try:
                    result = _run([bin_exiftool, "-json", in_path], timeout=10)
                    data = json.loads(result.stdout)
                    if data and isinstance(data, list):
                        return data[0]
                except Exception:
                    pass

            # Fallback: parse raw EXIF from JPEG header
            return self._parse_jpeg_exif(in_path) if in_path.lower().endswith((".jpg", ".jpeg")) else {}
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)

    def _parse_jpeg_exif(self, path: str) -> dict[str, Any]:
        """Minimal JPEG EXIF parser (stdlib only)."""
        tags: dict[str, Any] = {}
        try:
            with open(path, "rb") as f:
                data = f.read(65536)
            # Find APP1 marker
            pos = 2  # skip SOI
            while pos < len(data) - 4:
                if data[pos] != 0xFF:
                    break
                marker = data[pos + 1]
                if marker == 0xE1:  # APP1
                    length = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
                    exif_data = data[pos + 4 : pos + 2 + length]
                    if exif_data[:6] == b"Exif\x00\x00":
                        tags["_raw_exif"] = True
                        break
                    pos += 2 + length
                elif marker in (0xDA, 0xD9):
                    break
                else:
                    length = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
                    pos += 2 + length
        except Exception:
            pass
        return tags

    # ----------------------------------------------------------------
    # Base64 encode/decode
    # ----------------------------------------------------------------

    @staticmethod
    def encode_base64(data: bytes) -> str:
        """Encode bytes to base64 string."""
        return base64.b64encode(data).decode("ascii")

    @staticmethod
    def decode_base64(b64: str) -> bytes:
        """Decode bounded, valid base64 image data to bytes."""
        if len(b64) > _MAX_BASE64_ENCODED_CHARS:
            raise ValueError(f"base64 input exceeds {_MAX_BASE64_ENCODED_CHARS} characters")
        try:
            return base64.b64decode(b64, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid base64 data") from exc

    @staticmethod
    def to_data_url(data: bytes, mime: str = "image/png") -> str:
        """Wrap base64 in data URL prefix."""
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{mime};base64,{b64}"

    @staticmethod
    def from_data_url(data_url: str) -> tuple[bytes, str]:
        """Decode data URL to (bytes, mime_type)."""
        match = re.match(r"^data:([^;]+);base64,(.+)$", data_url, re.DOTALL)
        if not match:
            raise ValueError("Invalid data URL format")
        mime = match.group(1)
        payload = ImageProcessor.decode_base64(match.group(2))
        return payload, mime

    # ----------------------------------------------------------------
    # QR code generation (delegates to QRGenerator)
    # ----------------------------------------------------------------

    def generate_qr(
        self,
        text: str,
        *,
        scale: int = _DEFAULT_QR_SCALE,
        margin: int = _DEFAULT_QR_MARGIN,
        fill_color: str = "black",
        back_color: str = "white",
    ) -> bytes:
        """Generate QR code as PNG bytes. Convenience wrapper for QRGenerator."""
        qr = QRGenerator()
        return qr.generate(text, scale=scale, margin=margin, fill_color=fill_color, back_color=back_color)

    # ----------------------------------------------------------------
    # Vision model analysis (stub — requires external API key)
    # ----------------------------------------------------------------

    def analyze(
        self,
        path_or_bytes: Union[str, bytes],
        *,
        prompt: str = "Describe the image.",
        api_key: str | None = None,
        model: str = "claude-3-opus-20240229",
        max_tokens: int = 1024,
    ) -> str:
        """Analyze image via vision model (Anthropic/OpenAI). Requires API key."""
        import httpx as _httpx

        key = api_key or os.getenv("VISION_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            return "Error: No API key available. Set VISION_API_KEY or ANTHROPIC_API_KEY."

        if isinstance(path_or_bytes, bytes):
            raw = path_or_bytes
        else:
            try:
                if os.path.getsize(path_or_bytes) > _MAX_VISION_IMAGE_BYTES:
                    return f"Error: image exceeds {_MAX_VISION_IMAGE_BYTES} bytes"
                with open(path_or_bytes, "rb") as image_file:
                    raw = image_file.read(_MAX_VISION_IMAGE_BYTES + 1)
            except OSError as exc:
                return f"Error: unable to read image: {exc}"
        if len(raw) > _MAX_VISION_IMAGE_BYTES:
            return f"Error: image exceeds {_MAX_VISION_IMAGE_BYTES} bytes"
        b64 = self.encode_base64(raw)
        mime = _detect_mime_from_bytes(raw)

        # Anthropic API
        if os.getenv("ANTHROPIC_API_KEY") or "claude" in model.lower():
            headers = {
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime,
                                    "data": b64,
                                },
                            },
                        ],
                    }
                ],
            }
            try:
                resp = _httpx.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    content = result.get("content", [])
                    return content[0].get("text", "") if content else ""
                return f"Error: {resp.status_code} {resp.text[:300]}"
            except Exception as e:
                return f"Error: {e}"

        # OpenAI API fallback
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or "gpt-4o",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}",
                            },
                        },
                    ],
                }
            ],
        }
        try:
            resp = _httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                result = resp.json()
                choices = result.get("choices", [])
                return choices[0]["message"]["content"] if choices else ""
            return f"Error: {resp.status_code} {resp.text[:300]}"
        except Exception as e:
            return f"Error: {e}"


# ===================================================================
# PDFExtractor
# ===================================================================


@dataclass
class PdfMetadata:
    title: str = ""
    author: str = ""
    subject: str = ""
    creator: str = ""
    producer: str = ""
    creation_date: str = ""
    page_count: int = 0
    file_size: int = 0
    encrypted: bool = False


@dataclass
class PdfExtractionResult:
    text: str = ""
    page_count: int = 0
    metadata: PdfMetadata = field(default_factory=PdfMetadata)
    images: list[bytes] = field(default_factory=list)


class PDFExtractor:
    """PDF text/metadata extraction, to-image conversion, merge/split.

    Uses pdftotext (poppler-utils) and ghostscript for text extraction.
    """

    def __init__(self, tmp_dir: str | None = None):
        self._tmp_dir = tmp_dir or tempfile.mkdtemp(prefix="hellochus-pdf-")
        self._bin_pdftotext = _which("pdftotext")
        self._bin_gs = _which("gs") or _which("gswin64c")
        self._bin_pdfinfo = _which("pdfinfo")
        self._bin_pdftoppm = _which("pdftoppm")

    # ----------------------------------------------------------------
    # Text extraction
    # ----------------------------------------------------------------

    def extract_text(
        self,
        path_or_bytes: Union[str, bytes],
        *,
        page_range: str | None = None,
        password: str | None = None,
    ) -> PdfExtractionResult:
        """Extract text from PDF. page_range: '1-5', '1,3,5-7', etc."""
        tmp_in = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".pdf")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            result = PdfExtractionResult()
            result.metadata = self.extract_metadata(in_path)

            # Build pdftotext command
            cmd: list[str] = []
            if self._bin_pdftotext:
                cmd = [self._bin_pdftotext]
                if page_range:
                    cmd.extend(["-f", page_range.split("-")[0].split(",")[0]])
                    if "-" in page_range:
                        cmd.extend(["-l", page_range.split("-")[-1]])
                if password:
                    cmd.extend(["-pw", password])
                cmd.extend([in_path, "-"])
            elif self._bin_gs:
                # Ghostscript fallback for text extraction
                tmp_txt = _tmp_path(".txt")
                try:
                    cmd = [
                        self._bin_gs,
                        "-sDEVICE=txtwrite",
                        "-o", tmp_txt,
                        "-dNOPAUSE", "-dBATCH",
                        in_path,
                    ]
                    _run(cmd, timeout=60)
                    with open(tmp_txt, "r", errors="replace") as f:
                        result.text = f.read()
                    return result
                finally:
                    if os.path.exists(tmp_txt):
                        os.unlink(tmp_txt)
            else:
                raise RuntimeError("No PDF text extractor available (install poppler-utils or ghostscript)")

            if cmd:
                try:
                    proc = _run(cmd, timeout=60)
                    result.text = proc.stdout.decode(errors="replace")
                except RuntimeError:
                    pass

            return result
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)

    def extract_text_from_pages(
        self,
        path_or_bytes: Union[str, bytes],
        pages: list[int] | None = None,
    ) -> str:
        """Extract text from specific pages."""
        tmp_in = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".pdf")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            if not self._bin_pdftotext:
                return self.extract_text(in_path).text

            texts: list[str] = []
            for page in pages:
                try:
                    proc = _run(
                        [self._bin_pdftotext, "-f", str(page), "-l", str(page), in_path, "-"],
                        timeout=30,
                    )
                    texts.append(proc.stdout.decode(errors="replace"))
                except Exception:
                    texts.append("")
            return "\n\n".join(texts)
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)

    # ----------------------------------------------------------------
    # Metadata extraction
    # ----------------------------------------------------------------

    def extract_metadata(self, path_or_bytes: Union[str, bytes]) -> PdfMetadata:
        """Extract PDF metadata via pdfinfo."""
        tmp_in = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".pdf")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            meta = PdfMetadata()
            meta.file_size = os.path.getsize(in_path) if os.path.exists(in_path) else len(path_or_bytes) if isinstance(path_or_bytes, bytes) else 0

            if self._bin_pdfinfo:
                try:
                    proc = _run([self._bin_pdfinfo, in_path], timeout=10)
                    info = proc.stdout.decode(errors="replace")
                    for line in info.splitlines():
                        if ":" in line:
                            key, _, val = line.partition(":")
                            key = key.strip().lower()
                            val = val.strip()
                            if key == "title":
                                meta.title = val
                            elif key == "author":
                                meta.author = val
                            elif key == "subject":
                                meta.subject = val
                            elif key == "creator":
                                meta.creator = val
                            elif key == "producer":
                                meta.producer = val
                            elif key == "creationdate":
                                meta.creation_date = val
                            elif key == "pages":
                                meta.page_count = int(val)
                            elif "encrypted" in key.lower():
                                meta.encrypted = "yes" in val.lower()
                except Exception:
                    pass

            # Ghostscript metadata fallback
            if not meta.title and self._bin_gs:
                try:
                    proc = _run(
                        [
                            self._bin_gs,
                            "-sDEVICE=txtwrite",
                            "-dNOPAUSE", "-dBATCH",
                            "-sOutputFile=/dev/null",
                            "-c", "true",
                            in_path,
                        ],
                        timeout=10,
                    )
                except Exception:
                    pass

            return meta
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)

    # ----------------------------------------------------------------
    # PDF to image conversion
    # ----------------------------------------------------------------

    def to_images(
        self,
        path_or_bytes: Union[str, bytes],
        *,
        format: str = "png",
        dpi: int = 150,
        pages: list[int] | None = None,
    ) -> list[bytes]:
        """Convert PDF pages to images. Returns list of image bytes."""
        tmp_in = None
        out_pattern = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".pdf")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            prefix = _tmp_path("")
            if os.path.exists(prefix):
                os.unlink(prefix)
            os.makedirs(prefix, exist_ok=True) if not os.path.exists(prefix) else None
            # Use a proper prefix directory
            prefix_dir = tempfile.mkdtemp(prefix="pdf2img-")
            out_pattern = os.path.join(prefix_dir, "page")

            images: list[bytes] = []

            if self._bin_pdftoppm:
                cmd = [self._bin_pdftoppm, "-r", str(dpi), "-" + format, in_path, out_pattern]
                if pages:
                    for page in pages:
                        cmd = [self._bin_pdftoppm, "-r", str(dpi), "-f", str(page), "-l", str(page), "-" + format, in_path, out_pattern]
                        _run(cmd, timeout=120)
                        for fname in sorted(os.listdir(prefix_dir)):
                            if fname.endswith(f".{format}") or fname.endswith(f".{format[0].upper() + format[1:]}"):
                                fpath = os.path.join(prefix_dir, fname)
                                with open(fpath, "rb") as f:
                                    images.append(f.read())
                                os.unlink(fpath)
                else:
                    _run(cmd, timeout=120)
                    for fname in sorted(os.listdir(prefix_dir)):
                        if fname.endswith(f".{format}") or fname.endswith(f".{format[0].upper() + format[1:]}"):
                            fpath = os.path.join(prefix_dir, fname)
                            with open(fpath, "rb") as f:
                                images.append(f.read())

                return images

            if self._bin_gs:
                cmd = [
                    self._bin_gs,
                    f"-sDEVICE={'png16m' if format == 'png' else 'jpeg'}",
                    f"-r{dpi}",
                    "-o", f"{out_pattern}-%03d.{format}",
                    "-dNOPAUSE", "-dBATCH",
                    in_path,
                ]
                _run(cmd, timeout=120)
                for fname in sorted(os.listdir(prefix_dir)):
                    if fname.endswith(f".{format}"):
                        fpath = os.path.join(prefix_dir, fname)
                        with open(fpath, "rb") as f:
                            images.append(f.read())
                return images

            raise RuntimeError("No PDF to image converter available (install poppler-utils or ghostscript)")
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)
            if out_pattern:
                prefix_dir = os.path.dirname(out_pattern)
                if os.path.isdir(prefix_dir):
                    shutil.rmtree(prefix_dir, ignore_errors=True)

    # ----------------------------------------------------------------
    # PDF merging
    # ----------------------------------------------------------------

    def merge(self, pdf_paths: list[Union[str, bytes]], output_path: str) -> str:
        """Merge multiple PDFs into one. Returns output path."""
        tmp_files: list[str] = []
        try:
            resolved: list[str] = []
            for item in pdf_paths:
                if isinstance(item, bytes):
                    tmp = _tmp_path(".pdf")
                    with open(tmp, "wb") as f:
                        f.write(item)
                    tmp_files.append(tmp)
                    resolved.append(tmp)
                else:
                    resolved.append(str(item))

            if self._bin_gs:
                cmd = [
                    self._bin_gs,
                    "-sDEVICE=pdfwrite",
                    "-dNOPAUSE", "-dBATCH",
                    "-dSAFER",
                    f"-sOutputFile={output_path}",
                ] + resolved
                _run(cmd, timeout=120)
                return output_path

            if self._bin_pdftotext:
                # pdftotext doesn't merge, but we can try with ghostscript
                # If neither available, just concatenate (basic fallback)
                with open(output_path, "wb") as out:
                    for p in resolved:
                        with open(p, "rb") as inp:
                            out.write(inp.read())
                return output_path

            raise RuntimeError("No PDF merge tool available (install ghostscript)")
        finally:
            for f in tmp_files:
                if os.path.exists(f):
                    os.unlink(f)

    # ----------------------------------------------------------------
    # PDF splitting
    # ----------------------------------------------------------------

    def split(
        self,
        path_or_bytes: Union[str, bytes],
        *,
        output_dir: str | None = None,
    ) -> list[str]:
        """Split PDF into individual pages. Returns list of output paths."""
        tmp_in = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".pdf")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            if not output_dir:
                output_dir = tempfile.mkdtemp(prefix="pdf-split-")
            os.makedirs(output_dir, exist_ok=True)

            outputs: list[str] = []
            meta = self.extract_metadata(in_path)
            total_pages = meta.page_count or 1

            if self._bin_gs:
                for i in range(1, total_pages + 1):
                    out = os.path.join(output_dir, f"page_{i:03d}.pdf")
                    cmd = [
                        self._bin_gs,
                        "-sDEVICE=pdfwrite",
                        "-dNOPAUSE", "-dBATCH", "-dSAFER",
                        f"-dFirstPage={i}",
                        f"-dLastPage={i}",
                        f"-sOutputFile={out}",
                        in_path,
                    ]
                    _run(cmd, timeout=60)
                    if os.path.exists(out):
                        outputs.append(out)
                return outputs

            raise RuntimeError("No PDF split tool available (install ghostscript)")
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)


# ===================================================================
# AudioProcessor
# ===================================================================


@dataclass
class AudioMetadata:
    duration_ms: int = 0
    format: str = ""
    codec: str = ""
    sample_rate: int = 0
    channels: int = 0
    bitrate: int = 0
    file_size: int = 0


class AudioProcessor:
    """    Audio processing via ffmpeg/ffprobe: format detection, duration,
    transcription, chunking.
    """

    def __init__(self, tmp_dir: str | None = None):
        self._tmp_dir = tmp_dir or tempfile.mkdtemp(prefix="hellochus-audio-")
        self._bin_ffprobe = _which("ffprobe")
        self._bin_ffmpeg = _which("ffmpeg")

    # ----------------------------------------------------------------
    # Format detection / metadata
    # ----------------------------------------------------------------

    def probe(self, path_or_bytes: Union[str, bytes]) -> AudioMetadata:
        """Probe audio file for metadata."""
        tmp_in = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            meta = AudioMetadata()
            if os.path.exists(in_path):
                meta.file_size = os.path.getsize(in_path)

            if self._bin_ffprobe:
                try:
                    result = _run(
                        [
                            self._bin_ffprobe,
                            "-v", "error",
                            "-show_entries",
                            "format=format_name,duration,bit_rate:stream=codec_name,sample_rate,channels,codec_type",
                            "-of", "json",
                            in_path,
                        ],
                        timeout=15,
                    )
                    data = json.loads(result.stdout)
                    fmt = data.get("format", {})
                    meta.format = fmt.get("format_name", "")
                    duration_s = fmt.get("duration")
                    if duration_s:
                        meta.duration_ms = int(float(duration_s) * 1000)
                    meta.bitrate = int(fmt.get("bit_rate", 0))

                    for stream in data.get("streams", []):
                        if stream.get("codec_type") == "audio":
                            meta.codec = stream.get("codec_name", "")
                            meta.sample_rate = int(stream.get("sample_rate", 0))
                            meta.channels = int(stream.get("channels", 0))
                            break
                    return meta
                except Exception:
                    pass

            # Magic number detection fallback
            if isinstance(path_or_bytes, bytes):
                data = path_or_bytes
            else:
                with open(in_path, "rb") as f:
                    data = f.read(16)
            detected = _detect_mime_from_bytes(data)
            meta.format = detected
            return meta
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)

    def detect_format(self, data: bytes) -> str:
        """Detect audio format from bytes."""
        return _detect_mime_from_bytes(data)

    def is_voice_message_compatible(self, *, content_type: str | None = None, file_name: str | None = None) -> bool:
        """Check if audio is compatible with voice-message delivery paths."""
        if content_type:
            ct = content_type.strip().lower()
            if ct in _VOICE_MESSAGE_MIMES:
                return True
        if file_name:
            ext = os.path.splitext(file_name)[1].lower()
            if ext in _VOICE_MESSAGE_EXTENSIONS:
                return True
        return False

    # ----------------------------------------------------------------
    # Duration
    # ----------------------------------------------------------------

    def get_duration_ms(self, path_or_bytes: Union[str, bytes]) -> int:
        """Get audio duration in milliseconds."""
        meta = self.probe(path_or_bytes)
        return meta.duration_ms

    def get_duration_seconds(self, path_or_bytes: Union[str, bytes]) -> float:
        """Get audio duration in seconds."""
        return self.get_duration_ms(path_or_bytes) / 1000.0

    # ----------------------------------------------------------------
    # Transcription (subprocess to whisper or external)
    # ----------------------------------------------------------------

    def transcribe(
        self,
        path_or_bytes: Union[str, bytes],
        *,
        language: str = "en",
        model: str = "base",
    ) -> str:
        """Transcribe audio to text. Tries whisper CLI, then returns instruction."""
        tmp_in = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            # Try whisper CLI
            bin_whisper = _which("whisper")
            if bin_whisper:
                try:
                    result = _run(
                        [
                            bin_whisper,
                            in_path,
                            "--language", language,
                            "--model", model,
                            "--output_format", "txt",
                            "--output_dir", self._tmp_dir,
                        ],
                        timeout=300,
                    )
                    # Read output txt
                    base = os.path.splitext(os.path.basename(in_path))[0]
                    txt_path = os.path.join(self._tmp_dir, f"{base}.txt")
                    if os.path.exists(txt_path):
                        with open(txt_path, "r") as f:
                            return f.read()
                    return result.stdout.decode(errors="replace")
                except Exception as e:
                    return f"Transcription error: {e}"

            # Try openai-whisper (Python package)
            try:
                import whisper  # type: ignore
                result = whisper.load_model(model).transcribe(in_path, language=language)
                return result.get("text", "")
            except ImportError:
                pass

            return "Transcription requires whisper. Install: pip install openai-whisper"
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)

    # ----------------------------------------------------------------
    # Audio chunking
    # ----------------------------------------------------------------

    def chunk(
        self,
        path_or_bytes: Union[str, bytes],
        *,
        chunk_duration_ms: int = 30_000,
        overlap_ms: int = 0,
    ) -> list[bytes]:
        """Split audio into chunks of chunk_duration_ms milliseconds."""
        tmp_in = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            duration_ms = self.get_duration_ms(in_path)
            if duration_ms <= 0:
                return []

            chunks: list[bytes] = []
            start_ms = 0
            while start_ms < duration_ms:
                end_ms = min(start_ms + chunk_duration_ms, duration_ms)
                tmp_out = _tmp_path(".wav")

                if self._bin_ffmpeg:
                    start_s = start_ms / 1000.0
                    duration_s = (end_ms - start_ms) / 1000.0
                    _run(
                        [
                            self._bin_ffmpeg, "-y",
                            "-i", in_path,
                            "-ss", f"{start_s:.3f}",
                            "-t", f"{duration_s:.3f}",
                            "-acodec", "pcm_s16le",
                            "-ar", "16000",
                            "-ac", "1",
                            tmp_out,
                        ],
                        timeout=30,
                    )
                    with open(tmp_out, "rb") as f:
                        chunks.append(f.read())
                os.unlink(tmp_out)

                start_ms += chunk_duration_ms - overlap_ms
                if start_ms >= duration_ms:
                    break

            return chunks
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)

    # ----------------------------------------------------------------
    # Format conversion
    # ----------------------------------------------------------------

    def convert_format(
        self,
        path_or_bytes: Union[str, bytes],
        to_format: str = "wav",
        *,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> bytes:
        """Convert audio to target format."""
        tmp_in = None
        tmp_out = None
        try:
            if isinstance(path_or_bytes, bytes):
                tmp_in = _tmp_path(".bin")
                with open(tmp_in, "wb") as f:
                    f.write(path_or_bytes)
                in_path = tmp_in
            else:
                in_path = str(path_or_bytes)

            ext = _mime_to_ext(f"audio/{to_format}")
            if ext == ".bin":
                ext = f".{to_format}"
            tmp_out = _tmp_path(ext)

            if not self._bin_ffmpeg:
                raise RuntimeError("ffmpeg not found on PATH")

            _run(
                [
                    self._bin_ffmpeg, "-y",
                    "-i", in_path,
                    "-ar", str(sample_rate),
                    "-ac", str(channels),
                    tmp_out,
                ],
                timeout=60,
            )
            with open(tmp_out, "rb") as f:
                return f.read()
        finally:
            if tmp_in and os.path.exists(tmp_in):
                os.unlink(tmp_in)
            if tmp_out and os.path.exists(tmp_out):
                os.unlink(tmp_out)


# ===================================================================
# QRGenerator
# ===================================================================


class QRGenerator:
    """QR code generation using qrencode subprocess or qrcode Python package.

    Bounded scale/margin options with temp-file output.
    """

    def __init__(self, tmp_dir: str | None = None):
        self._tmp_dir = tmp_dir or tempfile.mkdtemp(prefix="hellochus-qr-")
        self._bin_qrencode = _which("qrencode")

    def _validate_int(self, name: str, value: int, default: int, min_val: int, max_val: int) -> int:
        """Validate bounded integer option for QR generation."""
        if value is None:
            return default
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"{name} must be a finite number")
        value = int(value)
        if value < min_val or value > max_val:
            raise ValueError(f"{name} must be between {min_val} and {max_val}")
        return value

    def generate(
        self,
        text: str,
        *,
        scale: int = _DEFAULT_QR_SCALE,
        margin: int = _DEFAULT_QR_MARGIN,
        fill_color: str = "black",
        back_color: str = "white",
    ) -> bytes:
        """Generate QR code as PNG bytes with validation."""
        scale = self._validate_int("scale", scale, _DEFAULT_QR_SCALE, _MIN_QR_SCALE, _MAX_QR_SCALE)
        margin = self._validate_int("margin", margin, _DEFAULT_QR_MARGIN, _MIN_QR_MARGIN, _MAX_QR_MARGIN)

        # Try qrencode subprocess
        if self._bin_qrencode:
            tmp_out = _tmp_path(".png")
            try:
                _run(
                    [
                        self._bin_qrencode,
                        "-o", tmp_out,
                        "-s", str(scale),
                        "-m", str(margin),
                        f"--foreground={fill_color}" if fill_color != "black" else "",
                        f"--background={back_color}" if back_color != "white" else "",
                        text,
                    ],
                    timeout=30,
                )
                with open(tmp_out, "rb") as f:
                    return f.read()
            except Exception:
                pass
            finally:
                if os.path.exists(tmp_out):
                    os.unlink(tmp_out)

        # Fallback: Python qrcode package
        try:
            import qrcode as _qrcode
            qr = _qrcode.QRCode(
                version=None,
                error_correction=_qrcode.constants.ERROR_CORRECT_L,
                box_size=scale,
                border=margin,
            )
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color=fill_color, back_color=back_color)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except ImportError:
            pass

        # Minimal QR-like placeholder using base64-encoded marker
        raise RuntimeError(
            "No QR generator available. Install: sudo apt install qrencode OR pip install qrcode[pil]"
        )

    def generate_data_url(
        self,
        text: str,
        *,
        scale: int = _DEFAULT_QR_SCALE,
        margin: int = _DEFAULT_QR_MARGIN,
        fill_color: str = "black",
        back_color: str = "white",
    ) -> str:
        """Generate QR as PNG data URL."""
        png = self.generate(text, scale=scale, margin=margin, fill_color=fill_color, back_color=back_color)
        b64 = base64.b64encode(png).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def generate_base64(
        self,
        text: str,
        *,
        scale: int = _DEFAULT_QR_SCALE,
        margin: int = _DEFAULT_QR_MARGIN,
    ) -> str:
        """Generate QR as raw PNG base64."""
        png = self.generate(text, scale=scale, margin=margin)
        return base64.b64encode(png).decode("ascii")

    def write_temp_file(
        self,
        text: str,
        *,
        scale: int = _DEFAULT_QR_SCALE,
        margin: int = _DEFAULT_QR_MARGIN,
        file_name: str = "qr.png",
    ) -> tuple[str, str]:
        """Write QR PNG to temp dir. Returns (file_path, dir_path)."""
        if not file_name or file_name in (".", "..") or os.path.dirname(file_name):
            raise ValueError("file_name must be a simple filename segment")

        png = self.generate(text, scale=scale, margin=margin)
        dir_path = tempfile.mkdtemp(prefix="qr-", dir=self._tmp_dir)
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, "wb") as f:
            f.write(png)
        return file_path, dir_path


# ===================================================================
# MediaStore
# ===================================================================


@dataclass
class MediaEntry:
    key: str
    path: str
    mime_type: str
    size: int
    created_at: float
    metadata: dict[str, Any] = field(default_factory=dict)


class MediaStore:
    """Media file storage with caching, cleanup, and type detection.

    Keyed storage, cache TTL, temp cleanup, content-based MIME detection.
    """

    def __init__(
        self,
        store_dir: str | None = None,
        *,
        cache_ttl_seconds: int = 86400,
        max_cache_size_bytes: int = 500 * 1024 * 1024,  # 500MB
    ):
        self._store_dir = store_dir or tempfile.mkdtemp(prefix="media-store-")
        self._cache_ttl = cache_ttl_seconds
        self._max_cache_size = max_cache_size_bytes
        self._index: dict[str, MediaEntry] = {}
        os.makedirs(self._store_dir, exist_ok=True)

    @property
    def store_dir(self) -> str:
        return self._store_dir

    # ----------------------------------------------------------------
    # Store / retrieve
    # ----------------------------------------------------------------

    def store(
        self,
        data: bytes,
        *,
        key: str | None = None,
        mime_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MediaEntry:
        """Store media bytes, return entry with key and path."""
        if not key:
            key = hashlib.sha256(data).hexdigest()[:16]

        if not mime_type:
            mime_type = _detect_mime_from_bytes(data)

        ext = _mime_to_ext(mime_type)
        file_path = os.path.join(self._store_dir, f"{key}{ext}")

        with open(file_path, "wb") as f:
            f.write(data)

        entry = MediaEntry(
            key=key,
            path=file_path,
            mime_type=mime_type,
            size=len(data),
            created_at=time.time(),
            metadata=metadata or {},
        )
        self._index[key] = entry
        return entry

    def get(self, key: str) -> MediaEntry | None:
        """Retrieve media entry by key."""
        entry = self._index.get(key)
        if not entry:
            # Try scanning disk
            for fname in os.listdir(self._store_dir):
                if fname.startswith(key):
                    fpath = os.path.join(self._store_dir, fname)
                    if os.path.isfile(fpath):
                        data = open(fpath, "rb").read()
                        mime = _detect_mime_from_bytes(data)
                        entry = MediaEntry(
                            key=key,
                            path=fpath,
                            mime_type=mime,
                            size=len(data),
                            created_at=os.path.getmtime(fpath),
                        )
                        self._index[key] = entry
                        break
        return entry

    def get_bytes(self, key: str) -> bytes | None:
        """Retrieve stored bytes by key."""
        entry = self.get(key)
        if not entry or not os.path.exists(entry.path):
            return None
        with open(entry.path, "rb") as f:
            return f.read()

    def get_as_data_url(self, key: str) -> str | None:
        """Retrieve stored media as data URL."""
        entry = self.get(key)
        if not entry:
            return None
        data = self.get_bytes(key)
        if not data:
            return None
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{entry.mime_type};base64,{b64}"

    def delete(self, key: str) -> bool:
        """Delete media entry by key."""
        entry = self._index.pop(key, None)
        if entry and os.path.exists(entry.path):
            os.unlink(entry.path)
            return True
        return False

    def store_file(self, file_path: str, *, key: str | None = None) -> MediaEntry:
        """Store an existing file by copying it into the store."""
        with open(file_path, "rb") as f:
            data = f.read()
        mime = _detect_mime_from_bytes(data)
        if not key:
            key = hashlib.sha256(data).hexdigest()[:16]
        return self.store(data, key=key, mime_type=mime)

    # ----------------------------------------------------------------
    # Type detection
    # ----------------------------------------------------------------

    @staticmethod
    def detect_type(data: bytes) -> str:
        """Detect media type from content bytes."""
        return _detect_mime_from_bytes(data)

    @staticmethod
    def detect_type_from_file(file_path: str) -> str:
        """Detect media type from file content."""
        with open(file_path, "rb") as f:
            header = f.read(32)
        return _detect_mime_from_bytes(header)

    # ----------------------------------------------------------------
    # Cache management
    # ----------------------------------------------------------------

    def cleanup_expired(self) -> int:
        """Remove entries older than cache_ttl. Returns count removed."""
        now = time.time()
        expired = [
            key for key, entry in self._index.items()
            if (now - entry.created_at) > self._cache_ttl
        ]
        for key in expired:
            self.delete(key)
        return len(expired)

    def cleanup_exceeding_size(self) -> int:
        """Remove oldest entries until total size <= max_cache_size. Returns count removed."""
        entries = sorted(self._index.values(), key=lambda e: e.created_at)
        total = sum(e.size for e in entries)
        removed = 0
        while total > self._max_cache_size and entries:
            entry = entries.pop(0)
            total -= entry.size
            self.delete(entry.key)
            removed += 1
        return removed

    def cleanup_temp(self) -> int:
        """Remove orphaned temp files in store dir. Returns count removed."""
        count = 0
        for fname in os.listdir(self._store_dir):
            fpath = os.path.join(self._store_dir, fname)
            if os.path.isfile(fpath) and fname.endswith(".tmp"):
                os.unlink(fpath)
                count += 1
        return count

    def cleanup_all(self) -> dict[str, int]:
        """Run all cleanup routines. Returns counts."""
        return {
            "expired": self.cleanup_expired(),
            "size_trimmed": self.cleanup_exceeding_size(),
            "temp_removed": self.cleanup_temp(),
        }

    def clear(self) -> int:
        """Remove all stored media. Returns count removed."""
        count = len(self._index)
        keys = list(self._index.keys())
        for key in keys:
            self.delete(key)
        return count

    # ----------------------------------------------------------------
    # List
    # ----------------------------------------------------------------

    def list_entries(self, mime_filter: str | None = None) -> list[MediaEntry]:
        """List all stored entries, optionally filtered by MIME type."""
        entries = list(self._index.values())
        if mime_filter:
            entries = [e for e in entries if mime_filter in e.mime_type]
        return entries

    @property
    def total_size(self) -> int:
        """Total size of all stored media in bytes."""
        return sum(e.size for e in self._index.values())

    @property
    def count(self) -> int:
        """Number of stored entries."""
        return len(self._index)


# ===================================================================
# Module-level convenience
# ===================================================================

# Global instances for quick access
image_processor = ImageProcessor()
pdf_extractor = PDFExtractor()
audio_processor = AudioProcessor()
qr_generator = QRGenerator()
media_store = MediaStore()
