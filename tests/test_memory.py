"""会话记忆单测。"""

from ai_platform.memory import MemoryStore


def test_roundtrip():
    m = MemoryStore()
    cid = m.new_conversation()
    m.add(cid, "user", "q")
    m.add(cid, "assistant", "a")
    hist = m.history(cid)
    assert len(hist) == 2
    assert hist[0]["role"] == "user"
    assert hist[1]["content"] == "a"
