from typing import List, Dict

Message = Dict[str, str]


class AgentMemory:
    def __init__(self, max_turns: int = 8, max_chars: int = 8000):
        self.history = List[Message] = []
        self.max_turns = max_turns
        self.max_chars = max_chars

    def add(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        self._trim()

    def get(self) -> List[Message]:
        return list(self.history)

    def clear(self):
        self.history = []

    def _trim(self):
        # 1) cap by turns
        while len(self.history) > self.max_turns * 2:  # user+assistant pair
            self.history.pop(0)
        # 2) cap by chars (rough token proxy): pop conversations until total content < max_chars
        total = sum(len(m["content"]) for m in self.history)
        while total > self.max_chars and self.history:
            removed = self.history.pop(0)
            total -= len(removed["content"])


class MemoryStore:
    """Simple in process store. 1 memory per session_id"""

    def __init__(self):
        self._store: Dict[str, AgentMemory] = {}

    def get(self, session_id: str) -> AgentMemory:
        if session_id not in self._store:
            self._store[session_id] = AgentMemory()
        return self._store[session_id]

    def reset(self, session_id: str):
        self._store.pop(session_id, None)
