"""The shift report's summary in the owner's language (scripts/paper_forward_shift.py): the same figures as the
sections under it, and a figure that cannot be read is said to be unreadable, never shown as a zero (rule 6)."""

from __future__ import annotations

from scripts.paper_forward_shift import UNREAD, arabic_summary


def view(**over):
    v = {"account": {"equity": 191_991.32},
         "period": {"id": "h1-confident-2026-11-01", "starts": "2026-11-01T22:00:00Z", "equity": 199_781.62,
                    "total_pnl": -218.38, "closed_pnl": -218.38, "open": 0, "performance": {"trades": 1}},
         "dual_ai": {"last_analysis": {"symbol": "EURGBP", "decision": "NO_TRADE",
                                       "consensus": {"rule": "LOW_CONFIDENCE"}},
                     "analyses": [{"symbol": "EURGBP"},
                                  {"symbol": "EURUSD", "time_machine": {"target_first": 0.31, "stop_first": 0.52,
                                                                        "neither": 0.17, "replays": 10_000,
                                                                        "verdict": "leans toward the stop"}}]}}
    return {**v, **over}


def test_the_summary_repeats_the_figures_and_the_last_decision_in_the_owners_language():
    text = "\n".join(arabic_summary(view()))
    assert "الرصيد $199,781.62" in text and "الربح أو الخسارة $-218.38" in text and "صفقات مسكّرة 1" in text
    assert "الحساب الكامل من البداية: $191,991.32" in text and "مو فلوس حقيقية" in text
    assert "EURGBP لا صفقة (اتفقوا بس مو الاثنين واثقين 65 أو أكثر)" in text  # not both: one under it is enough
    assert "(EURUSD، 10000 إعادة): الهدف أول 31%، الستوب أول 52%، ولا واحد 17%: يميل للستوب" in text


def test_an_unpriced_open_trade_reads_unreadable_never_zero():
    # 2026-11-02 08:59: an open position the broker could not value left the new account's equity unreadable
    unpriced = {**view()["period"], "equity": None, "total_pnl": None, "open": 2, "unpriced": 1}
    text = "\n".join(arabic_summary(view(period=unpriced, account={"available": False, "reason": "no quote"})))
    assert f"الرصيد {UNREAD}" in text and f"الربح أو الخسارة {UNREAD}" in text
    assert f"الحساب الكامل من البداية: {UNREAD}" in text and "$0.00" not in text and "n/a" not in text
    text = "\n".join(arabic_summary(view(period={"available": False, "reason": "unreadable"})))
    assert f"الحساب الجديد: {UNREAD}" in text


def test_no_time_machine_and_no_decision_yet_are_left_out_never_invented():
    text = "\n".join(arabic_summary(view(dual_ai={})))
    assert "آلة الزمن" not in text and "آخر قرار" not in text and "الحساب الكامل" in text


def test_the_summary_names_the_senior_its_refusals_and_its_spend_when_one_is_declared():
    senior = {"models": {"senior": "anthropic/claude-opus-5.5"}, "spent_total": 0.51, "total_usd": 8.5}
    dai = {**view()["dual_ai"], "openrouter": {"paid_trial": senior},
           "record": {"decisions_by_rule": {"SENIOR_VETO": 3, "SENIOR_UNAVAILABLE": 1, "AGREE": 2}}}
    text = "\n".join(arabic_summary(view(dual_ai=dai)))
    assert "claude-opus-5.5" in text and "رفض 3" in text and "ما جاوب 1" in text and "صرف $0.51 من $8.50" in text
    unread = {**dai, "openrouter": {"paid_trial": {**senior, "spent_total": None}}}
    assert f"صرف {UNREAD}" in "\n".join(arabic_summary(view(dual_ai=unread)))  # an unread spend is never $0.00
    assert "المتداول الكبير" not in "\n".join(arabic_summary(view()))  # none declared: nothing said
