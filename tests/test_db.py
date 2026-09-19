"""关系存储模块单测。"""

from ai_platform.db import Conversation, Message, get_session, init_db


def test_init_and_insert():
    init_db()
    with get_session() as s:
        s.add(Conversation(id="c1", title="t"))
        s.commit()
        s.add(Message(conv_id="c1", role="user", content="hi"))
        s.commit()
        rows = s.query(Message).filter_by(conv_id="c1").all()
        assert len(rows) == 1
        assert rows[0].content == "hi"
