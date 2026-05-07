try:
    import tiktoken
    _ENCODER = tiktoken.get_encoding("cl100k_base")
except ImportError:
    _ENCODER = None


class History:
    def __init__(self, max_entries: int = 20):
        self.messages = []
        self.max_entries = max_entries
        self.encoder = _ENCODER

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        # Keep only the last N entries to manage context size
        if len(self.messages) > self.max_entries and self.messages:
            # Remove oldest entries but keep at least the first (system) message if present
            if self.messages[0].get("role") == "system":
                self.messages = [self.messages[0]] + self.messages[-(self.max_entries-1):]
            else:
                self.messages = self.messages[-self.max_entries:]

    def get(self) -> list[dict]:
        return self.messages

    def clear(self):
        self.messages = []
        
    def get_token_count(self, messages: list[dict]) -> int:
        """Calculate the approximate token count for a list of messages."""
        text = " ".join([msg["content"] for msg in messages if msg.get("content")])
        if self.encoder:
            return len(self.encoder.encode(text))
        return len(text) // 4

    def optimize_context(self, max_tokens: int = 4000) -> list[dict]:
        """Optimize history to fit within max_tokens, prioritizing system and recent messages."""
        optimized_messages = []
        current_token_count = 0

        # Always include the system message if present
        if self.messages and self.messages[0].get("role") == "system":
            system_message = self.messages[0]
            optimized_messages.append(system_message)
            current_token_count += self.get_token_count([system_message])

        # Add recent messages until max_tokens is reached
        # Iterate backwards to prioritize most recent messages
        for message in reversed(self.messages):
            if message.get("role") == "system":
                continue # Already added
            
            message_token_count = self.get_token_count([message])
            
            # If adding this message exceeds the limit, stop
            if current_token_count + message_token_count > max_tokens:
                break
            
            # Add message to the beginning of the optimized list (after system message if present)
            if optimized_messages and optimized_messages[0].get("role") == "system":
                optimized_messages.insert(1, message)
            else:
                optimized_messages.insert(0, message)
            current_token_count += message_token_count
            
        # Ensure messages are in chronological order (system, then oldest to newest user/assistant)
        if optimized_messages and optimized_messages[0].get("role") == "system":
            return [optimized_messages[0]] + sorted(optimized_messages[1:], key=lambda x: self.messages.index(x))
        else:
            return sorted(optimized_messages, key=lambda x: self.messages.index(x))

    def get_user_inputs(self) -> list[str]:
        """Returns a list of all user inputs in the history."""
        return [msg["content"] for msg in self.messages if msg["role"] == "user"]
