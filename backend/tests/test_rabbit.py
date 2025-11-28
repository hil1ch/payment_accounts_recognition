import pytest
from app.core.rabbit_connection import rabbit_conn


@pytest.mark.asyncio
async def test_rabbit_connection(monkeypatch):
    calls = {"init": False, "close": False}

    async def fake_init():
        calls["init"] = True

    async def fake_close():
        calls["close"] = True

    monkeypatch.setattr(rabbit_conn, "init", fake_init)
    monkeypatch.setattr(rabbit_conn, "close", fake_close)

    await rabbit_conn.init()
    await rabbit_conn.close()

    assert calls["init"] is True
    assert calls["close"] is True
