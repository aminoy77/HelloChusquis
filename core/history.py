class History:
    def __init__(self, max_entries: int = 20):
        self.messages = []
        self.max_entries = max_entries

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        # Keep only the last N entries to manage context size
        if len(self.messages) > self.max_entries:
            # Remove oldest entries but keep at least the first (system) message if present
            if self.messages[0].get("role") == "system":
                self.messages = [self.messages[0]] + self.messages[-(self.max_entries-1):]
            else:
                self.messages = self.messages[-self.max_entries:]

    def get(self) -> list[dict]:
        return self.messages

    def clear(self):
        self.messages = []
        
    def get_context_size(self) -> int:
        """Calculate approximate token count of history"""
        total_chars = sum(len(msg["content"]) for msg in self.messages)
        # Rough approximation: 1 token ≈ 4 characters
        return total_chars // 4
    
    def optimize_context(self, max_tokens: int = 3000) -> list[dict]:
        """
        Return a optimized version of history that fits within token limits
        """
        if self.get_context_size() <= max_tokens:
            return self.messages
            
        # Start with system message if present
        optimized = []
        if self.messages and self.messages[0].get("role") == "system":
            optimized.append(self.messages[0])
            
        # Add recent messages until we approach token limit
        recent_messages = self.messages[-10:] if self.messages[0].get("role") == "system" else self.messages[-10:]
        
        current_tokens = self.get_context_size()
        for msg in reversed(recent_messages):
            if msg.get("role") == "system":
                continue  # Already added
                
            msg_tokens = len(msg["content"]) // 4
            if len(optimized) >= 20 or (current_tokens + msg_tokens) > max_tokens * 0.8:
                break
                
            optimized.insert(1 if optimized and optimized[0].get("role") == "system" else 0, msg)
            
        return optimized