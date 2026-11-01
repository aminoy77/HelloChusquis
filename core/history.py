_ENCODER = None
_ENCODER_LOADED = False


def _get_encoder():
    """Load tiktoken lazily: BPE ranks cost ~90ms, only needed for counts."""
    global _ENCODER, _ENCODER_LOADED
    if not _ENCODER_LOADED:
        _ENCODER_LOADED = True
        try:
            import tiktoken
            _ENCODER = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            _ENCODER = None
    return _ENCODER


class History:
    def __init__(self, max_entries: int = 100):
        self.messages: list[dict] = []
        self.max_entries = max_entries
        self.encoder = _ENCODER
        self._timestamps: list[float] = []

    def _now(self) -> float:
        """Return current timestamp."""
        import time
        return time.time()

    def add(self, role: str, content: str):
        """Add message. Backward compatible with existing calls."""
        self.messages.append({"role": role, "content": content})
        self._timestamps.append(self._now())
        self._trim()

    def _trim(self):
        """Keep only last max_entries, always preserving first system message."""
        if len(self.messages) <= self.max_entries:
            return
        if self.messages and self.messages[0].get("role") == "system":
            if self.max_entries == 1:
                self.messages = [self.messages[0]]
                self._timestamps = [self._timestamps[0]]
            else:
                self.messages = [self.messages[0]] + self.messages[-(self.max_entries - 1):]
                self._timestamps = [self._timestamps[0]] + self._timestamps[-(self.max_entries - 1):]
        else:
            self.messages = self.messages[-self.max_entries:]
            self._timestamps = self._timestamps[-self.max_entries:]

    def get(self) -> list[dict]:
        """Return messages. Backward compatible."""
        return self.messages

    def clear(self):
        """Clear all history."""
        self.messages = []
        self._timestamps = []

    def get_token_count(self, messages: list[dict]) -> int:
        """Approximate token count for a list of messages."""
        text = " ".join([msg.get("content", "") for msg in messages if msg.get("content")])
        encoder = self.encoder or _get_encoder()
        if encoder:
            return len(encoder.encode(text))
        return len(text) // 4

    def optimize_context(self, max_tokens: int = 4000) -> list[dict]:
        """Optimize history to fit within max_tokens. Safe against missing messages."""
        optimized: list[dict] = []
        current_count = 0

        # Always include system message
        has_system = self.messages and self.messages[0].get("role") == "system"
        if has_system:
            system_msg = self.messages[0]
            optimized.append(system_msg)
            current_count += self.get_token_count([system_msg])

        # Build index map for safe ordering (avoids self.messages.index(x) ValueError)
        msg_index = {id(m): i for i, m in enumerate(self.messages)}

        # Add recent messages backwards
        for message in reversed(self.messages):
            if message.get("role") == "system":
                continue
            msg_tokens = self.get_token_count([message])
            if current_count + msg_tokens > max_tokens:
                break
            optimized.append(message)
            current_count += msg_tokens

        # Restore chronological order using index map (safe lookup)
        if has_system:
            system_msg = optimized[0]
            rest = sorted(optimized[1:], key=lambda m: msg_index.get(id(m), 0))
            return [system_msg] + rest
        else:
            return sorted(optimized, key=lambda m: msg_index.get(id(m), 0))

    def get_user_inputs(self) -> list[str]:
        """Return list of all user inputs."""
        return [msg.get("content", "") for msg in self.messages if msg.get("role") == "user"]
