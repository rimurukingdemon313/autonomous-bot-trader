"""Secrets never leave the process in a log line (SECURITY_CONTRACT.md §4)."""

from __future__ import annotations

import json

from aitrader.observability import PLACEHOLDER, log_event, recent

JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.c2lnbmF0dXJlLXZhbHVl"


def test_secret_env_values_token_shapes_and_secret_keys_are_redacted(monkeypatch, capsys):
    monkeypatch.setenv("TRADELOCKER_PASSWORD", "hunter2-not-real")
    monkeypatch.setenv("AI_API_KEY", "key-value-not-real-123")
    rec = log_event(
        "TEST", "login failed for password hunter2-not-real with Authorization: Bearer abc.def.ghi",
        response='{"accessToken": "tok-123", "status": "ok"}', jwt=JWT, nested={"apiKey": "x", "ok": 1},
        items=["key-value-not-real-123", "sk-abcdefghijklmnop"],
    )
    line = capsys.readouterr().out
    for leaked in ("hunter2-not-real", "abc.def.ghi", "tok-123", JWT, "key-value-not-real-123", "sk-abcdefghijklmnop"):
        assert leaked not in line, leaked
    body = json.loads(line.strip().splitlines()[-1])
    assert body["nested"]["apiKey"] == PLACEHOLDER and body["nested"]["ok"] == 1
    assert '"status": "ok"' in body["response"]  # only the secret is removed, not the context
    assert rec in recent(5)  # what the dashboard's log panel serves is the redacted record
    assert "hunter2-not-real" not in json.dumps(recent(5))


def test_short_or_empty_env_values_do_not_blank_every_line(monkeypatch, capsys):
    monkeypatch.setenv("DASHBOARD_TOKEN", "")
    monkeypatch.setenv("TRADELOCKER_EMAIL", "a")
    log_event("TEST", "a normal message about EURUSD")
    assert "a normal message about EURUSD" in capsys.readouterr().out
