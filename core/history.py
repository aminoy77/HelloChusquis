class History:
    def __init__(self):
        self.messages = []

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def get(self) -> list[dict]:
        return self.messages

    def clear(self):
        self.messages = []