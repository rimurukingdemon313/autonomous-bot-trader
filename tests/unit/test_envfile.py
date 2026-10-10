"""The local .env file: fills only what the environment lacks, reads quoted and commented values, and hands
back names, never values."""

from __future__ import annotations

from aitrader import envfile
from aitrader.llm.openrouter import OpenRouterConfig


def test_quoted_values_inline_comments_and_the_environment_wins(tmp_path):
    f = tmp_path / ".env"
    f.write_text('# comment\nOPENROUTER_API_KEY="sk-or-v1-abc#def"\nMODE=PAPER_FORWARD   # paper only\n'
                 "export DECISION_MODE='dual_ai'\nSYMBOLS=EURUSD,GBPUSD\nbroken line\nMODE=LIVE\n")
    env = {"SYMBOLS": "USDJPY"}
    names = envfile.load(f, env)
    assert env["OPENROUTER_API_KEY"] == "sk-or-v1-abc#def"  # a # inside quotes is part of the value
    assert env["MODE"] == "PAPER_FORWARD"                    # the first occurrence; the later LIVE line is ignored
    assert env["DECISION_MODE"] == "dual_ai" and env["SYMBOLS"] == "USDJPY"  # the environment wins
    assert sorted(names) == ["DECISION_MODE", "MODE", "OPENROUTER_API_KEY"]
    assert all("sk-or" not in n for n in names)


def test_a_missing_file_changes_nothing_and_the_template_key_is_not_configured(tmp_path):
    env: dict = {}
    assert envfile.load(tmp_path / "nope.env", env) == [] and env == {}
    f = tmp_path / ".env"
    f.write_text('OPENROUTER_API_KEY="PASTE_MY_KEY_HERE"\n')
    envfile.load(f, env)
    assert not OpenRouterConfig.from_env(env).configured


def test_the_example_file_carries_the_key_placeholder_and_no_real_key():
    from pathlib import Path
    text = (Path(__file__).resolve().parents[2] / ".env.example").read_text()
    assert 'OPENROUTER_API_KEY="PASTE_MY_KEY_HERE"' in text
    assert "sk-or-v1-" not in text
