try:
    import tiktoken
    _ENCODER = tiktoken.get_encoding("cl100k_base")
except ImportError:
    _ENCODER = None


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

    def add_system_message(self, content: str):
        """Add system message. Always inserts at position 0."""
        self.messages.insert(0, {"role": "system", "content": content})
        self._timestamps.insert(0, self._now())
        self._trim()

    def _trim(self):
        """Keep only last max_entries, always preserving first system message."""
        if len(self.messages) <= self.max_entries:
            return
        if self.messages and self.messages[0].get("role") == "system":
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
        if self.encoder:
            return len(self.encoder.encode(text))
        return len(text) // 4

    def get_stats(self) -> dict:
        """Return stats about current history."""
        return {
            "total_messages": len(self.messages),
            "total_tokens": self.get_token_count(self.messages),
            "oldest_timestamp": self._timestamps[0] if self._timestamps else None,
        }

    def _summarize_pair(self, user_msg: dict, assistant_msg: dict) -> dict:
        """Summarize a user+assistant pair into a single short line."""
        user_content = user_msg.get("content", "")[:80]
        assistant_content = assistant_msg.get("content", "")[:80]
        summary = (
            f"[Summary] User asked about: {user_content}... "
            f"-> Assistant responded about: {assistant_content}..."
        )
        return {"role": "system", "content": summary}

    def compress_if_needed(self, max_tokens: int = 8000) -> list[dict]:
        """Intelligently compress history if over token budget.

        Strategy:
        - Keep system message always
        - Keep last 5 messages in full
        - Summarize middle pairs (user+assistant) into 1-line summaries
        """
        total = self.get_token_count(self.messages)
        if total <= max_tokens:
            return self.messages

        compressed: list[dict] = []
        system_idx = 0

        # Extract system message
        has_system = self.messages and self.messages[0].get("role") == "system"
        if has_system:
            compressed.append(self.messages[0])
            system_idx = 1

        # Remaining messages (excluding system)
        remaining = self.messages[system_idx:]
        if len(remaining) <= 5:
            # Few enough messages, keep all
            compressed.extend(remaining)
            return compressed

        # Keep last 5 in full
        tail = remaining[-5:]
        middle = remaining[:-5]

        # Summarize middle in pairs
        summarized: list[dict] = []
        i = 0
        while i < len(middle):
            if (
                i + 1 < len(middle)
                and middle[i].get("role") == "user"
                and middle[i + 1].get("role") == "assistant"
            ):
                summarized.append(self._summarize_pair(middle[i], middle[i + 1]))
                i += 2
            else:
                # Odd message out, keep as-is
                summarized.append(middle[i])
                i += 1

        compressed.extend(summarized)
        compressed.extend(tail)
        return compressed

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
