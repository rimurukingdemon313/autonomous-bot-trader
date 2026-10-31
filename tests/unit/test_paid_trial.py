"""The owner's paid trial, mocked: a paid model takes a trader's seat only inside its window, its declared prices and
its caps (read from the key's own spend); the FREE models stay its fallbacks; anything unexpected ends it or, for
spend nobody accounts for, stops every request. No test reaches openrouter.ai."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from aitrader.llm.openrouter import KEY_CHECK_S, OpenRouterClient, OpenRouterConfig
from aitrader.llm.paid_trial import PAID_TRIAL, PROMPT_TOKENS_RESERVE, PaidModel, PaidTrial, call_reserve

from tests.openrouter_kit import DEBATE, KEY, TRADER, VISION, model, ok

T0 = datetime(2026, 10, 26, 9, 0, tzinfo=timezone.utc).timestamp()  # a Monday morning inside the window
PV, PJ = "lab-a/paid-vision", "lab-b/paid-judge"
TRIAL = PaidTrial(name="test-trial", models={"vision": PaidModel(PV, 1.0, 2.0), "judge": PaidModel(PJ, 1.0, 2.0)},
                  starts="2026-10-26T00:00:00Z", ends="2026-10-31T00:00:00Z", total_usd=1.0, daily_usd=0.30,
                  max_call_usd=0.10)
MSG = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]


def paid(mid, prompt="0.000001", completion="0.000002", **extra):
    return {**model(mid, image=True, ii=45), "pricing": {"prompt": prompt, "completion": completion, **extra}}


def catalog(**over):
    return [model(VISION, image=True, ii=30), model(TRADER, image=False, ii=28), model(DEBATE, image=True, ii=15),
            over.get("pv", paid(PV)), over.get("pj", paid(PJ))]


def accept(d):
    return None


class Fake:
    """The catalog, a key whose spend rises by what each paid reply costs, and chat replies."""

    def __init__(self, cat=None, cost=0.01, daily_field=True, reply=None):
        self.catalog = catalog() if cat is None else cat
        self.cost, self.daily_field, self.reply = cost, daily_field, reply
        self.usage, self.daily, self.extra = 0.0, 0.0, 0.0
        self.calls: list[str] = []
        self.key_reads = 0

    def __call__(self, method, url, headers, body, timeout):
        if url.endswith("/models"):
            return 200, {}, {"data": self.catalog}
        if url.endswith("/key"):
            self.key_reads += 1
            d = {"label": "t", "usage": self.usage + self.extra, "is_free_tier": False}
            if self.daily_field:
                d["usage_daily"] = self.daily + self.extra
            return 200, {}, {"data": d}
        m = body["model"]
        self.calls.append(m)
        if self.reply is not None:
            out = self.reply(m, body)
            if out is not None:
                return out
        cost = self.cost if m in (PV, PJ) else 0
        self.usage += cost
        self.daily += cost
        return ok(json.dumps({"x": 1}), m, cost=cost)


def client(fake, t=None, trial=TRIAL, **cfg):
    now = [T0 if t is None else t]
    c = OpenRouterClient(OpenRouterConfig(api_key=KEY, **cfg), transport=fake, clock=lambda: now[0],
                         sleep=lambda s: None, trial=trial)
    return c, now


def ask(c, role, key="k"):
    return c.chat_json(role, MSG, accept, dedupe_key=key, max_tokens=1000)


# ── inside the window ────────────────────────────────────────────────────

def test_inside_the_window_each_traders_paid_model_answers_first_and_its_cost_is_recorded():
    fake = Fake()
    c, _ = client(fake)
    v, j, d = ask(c, "vision", "a"), ask(c, "judge", "b"), ask(c, "verifier", "c")
    assert (v.model, j.model) == (PV, PJ) and v.ok and j.ok
    assert v.cost == pytest.approx(0.01) and v.record()["cost"] == pytest.approx(0.01)
    assert d.model == DEBATE and d.cost == 0  # the debate is measurement only: never paid
    assert c.models_for("vision", 1000)[1:] == [VISION, DEBATE]  # the FREE models stay the fallbacks, in order
    st = c.trial_status()
    assert st["active"] and st["spent_by_this_process"] == pytest.approx(0.02) and st["reserved_unconfirmed"] == 0
    assert c.health()["status"] == "READY" and c.health()["paid_trial"]["models"] == {"vision": PV, "judge": PJ}


@pytest.mark.parametrize("t", [datetime(2026, 10, 25, 23, 59, tzinfo=timezone.utc).timestamp(),
                               datetime(2026, 10, 31, 0, 0, tzinfo=timezone.utc).timestamp()])
def test_outside_its_window_nothing_paid_is_asked(t):
    fake = Fake()
    c, _ = client(fake, t=t)
    assert ask(c, "vision").model == VISION and ask(c, "judge", "j").model == TRADER
    assert PV not in fake.calls and PJ not in fake.calls
    assert c.trial_status()["not_asked_because"]["vision"] == "outside its window"


def test_the_owner_can_switch_it_off_and_nothing_in_the_environment_can_start_it():
    assert OpenRouterConfig.from_env({"OPENROUTER_PAID_TRIAL": "off"}).paid_trial_off is True
    assert OpenRouterConfig.from_env({"OPENROUTER_PAID_TRIAL": "on"}).paid_trial_off is False
    fake = Fake()
    c, _ = client(fake, paid_trial_off=True)
    assert ask(c, "vision").model == VISION and PV not in fake.calls
    none, _ = client(Fake(), trial=PaidTrial(name="none"))  # no trial declared: FREE ONLY
    assert ask(none, "vision").model == VISION


# ── the caps, read from the key's own spend ──────────────────────────────

def test_todays_share_stops_paid_calls_until_the_next_utc_day():
    fake = Fake()
    fake.daily = fake.usage = TRIAL.daily_usd - 0.001  # the key says today is all but spent
    c, now = client(fake)
    res = ask(c, "vision")
    assert res.model == VISION and PV not in fake.calls  # the next call could cross today's share
    assert "today's share is spent" in c.trial_status()["not_asked_because"]["vision"]
    now[0] = datetime(2026, 10, 27, 0, 5, tzinfo=timezone.utc).timestamp()  # a new UTC day
    fake.daily = 0.0
    assert ask(c, "vision", "next-day").model == PV  # its spend read anew before anything paid is asked


def test_spend_since_the_last_key_read_counts_against_the_caps_before_the_next_read():
    fake = Fake(cost=0.09)
    c, _ = client(fake)
    asked = [ask(c, "vision", f"k{i}").model for i in range(5)]
    # the key is read once (every KEY_CHECK_S); this process's own spend since then still counts
    assert asked[:3] == [PV, PV, PV] and asked[3:] == [VISION, VISION]  # 3 x 0.09 + the next reserve > 0.30
    assert c.trial_status()["spent_by_this_process"] == pytest.approx(0.27)


def test_the_total_stops_paid_calls_for_good():
    fake = Fake()
    fake.usage = TRIAL.total_usd - 0.001
    c, _ = client(fake)
    assert ask(c, "judge").model == TRADER and PJ not in fake.calls
    assert "its total is spent" in c.trial_status()["not_asked_because"]["judge"]


def test_without_the_keys_daily_spend_nothing_paid_is_asked():
    fake = Fake(daily_field=False)
    c, _ = client(fake)
    assert ask(c, "vision").model == VISION and PV not in fake.calls
    assert "not read for today" in c.trial_status()["not_asked_because"]["vision"]


def test_a_call_whose_cost_is_unknown_is_counted_at_its_most():
    def timeout_paid(m, body):
        if m == PV:
            raise TimeoutError("timed out")
        return None
    fake = Fake(reply=timeout_paid)
    c, _ = client(fake, max_retries=0)
    res = ask(c, "vision")
    assert res.model == VISION and fake.calls[0] == PV  # the paid model timed out, the free one answered
    reserve = call_reserve(paid(PV), 1000)
    assert reserve == pytest.approx(PROMPT_TOKENS_RESERVE * 1e-6 + 1000 * 2e-6)
    assert c.trial_status()["reserved_unconfirmed"] == pytest.approx(reserve)


# ── price and stops ──────────────────────────────────────────────────────

@pytest.mark.parametrize("pv,field", [(paid(PV, prompt="0.0000011"), "prompt"),
                                      (paid(PV, completion="0.0000021"), "completion"),
                                      (paid(PV, request="0.001"), "request"),
                                      (paid(PV, prompt="-1"), "prompt")])
def test_a_price_above_the_declared_one_keeps_the_paid_model_out(pv, field):
    fake = Fake(cat=catalog(pv=pv))
    c, _ = client(fake)
    assert ask(c, "vision").model == VISION and PV not in fake.calls
    assert field in c.trial_status()["not_asked_because"]["vision"]


def test_a_price_for_a_feature_the_client_never_uses_does_not_keep_the_model_out():
    # live 2026-10-26: anthropic/claude-haiku-5.5 lists web_search at $0.01 a search; the seat ran free all morning
    bodies = []

    def spy(m, body):
        bodies.append(body)
        return None
    # and then (1.2.0) input_cache_write_1h: only what a request can be charged is checked, whatever else is listed
    unused = dict(web_search="0.01", input_cache_write="0.0000005", input_cache_write_1h="0.0000002",
                  image_output="0.04", audio="0.0001", internal_reasoning_effort="?", discount="-1")
    fake = Fake(cat=catalog(pj=paid(PJ, **unused)), reply=spy)
    c, _ = client(fake)
    assert ask(c, "judge").model == PJ and c.trial_status()["not_asked_because"]["judge"] is None
    assert call_reserve(paid(PJ, **unused), 1000) == pytest.approx(call_reserve(paid(PJ), 1000))
    assert call_reserve(paid(PJ, request="0.001", image="0.002"), 1000) == pytest.approx(
        call_reserve(paid(PJ), 1000) + 0.003)  # what a request can be charged per item is reserved
    for k, v in (("input_cache_read", "0.0000011"), ("internal_reasoning", "0.0000021"), ("image", "0.001"),
                 ("request", "nan?")):  # and those prices are still checked against the declared ones
        assert paid(PJ, **{k: v}) and TRIAL.models["judge"].priced_as_declared(paid(PJ, **{k: v})), k
    for b in bodies:  # and no request can be charged for it: none asks for a search
        assert not {"plugins", "web_search_options"} & set(b) and not b["model"].endswith(":online")
    assert ask(client(Fake(cat=catalog(pj=paid(PJ, image="0.01"))))[0], "judge").model == TRADER  # an image is sent


#: the two models exactly as the public catalog priced them on 2026-10-26 (dual-ai-check-results a2879b4)
LIVE_PRICING = {
    "anthropic/claude-haiku-5.5": {"prompt": "0.0000001", "completion": "0.0000005", "web_search": "0.01",
                                   "input_cache_read": "0.00000001", "input_cache_write": "0.000000125",
                                   "input_cache_write_1h": "0.0000002",
                                   "overrides": [{"min_prompt_tokens": 100000, "prompt": "0.0000005",
                                                  "completion": "0.0000025", "input_cache_read": "0.00000005",
                                                  "input_cache_write": "0.000000625", "input_cache_write_1h": "0.000001"}]},
    "xiaomi/mimo-v2.6-pro": {"prompt": "0.000000435", "completion": "0.00000087", "input_cache_read": "0.0000000036"},
}


def test_the_declared_trials_models_pass_on_their_live_catalog_prices_and_a_call_stays_under_its_cap():
    for role, m in PAID_TRIAL.models.items():
        live = {"id": m.id, "pricing": LIVE_PRICING[m.id]}
        assert m.priced_as_declared(live) is None, (role, m.priced_as_declared(live))
        assert call_reserve(live, 12000) <= PAID_TRIAL.max_call_usd  # the most a call can cost, under the cap
    # Haiku's dearer tier starts at 100k prompt tokens; a trader's prompt is under a third of that
    assert PROMPT_TOKENS_RESERVE < LIVE_PRICING["anthropic/claude-haiku-5.5"]["overrides"][0]["min_prompt_tokens"]


def test_a_paid_model_missing_from_the_catalog_is_not_asked():
    fake = Fake(cat=catalog()[:3] + [paid(PJ)])
    c, _ = client(fake)
    assert ask(c, "vision").model == VISION and "not in the catalog" in c.trial_status()["not_asked_because"]["vision"]


def test_a_reply_costing_more_than_declared_is_discarded_and_ends_the_trial():
    fake = Fake(cost=0.25)  # above max_call_usd 0.10
    c, _ = client(fake)
    res = ask(c, "vision")
    assert res.ok and res.model == VISION and res.tried == [(PV, "NOT_AS_PRICED")]  # discarded; the free one answered
    assert ask(c, "judge", "j").model == TRADER and PJ not in fake.calls  # ended for every seat
    assert "stopped" in c.trial_status()["stopped"] and not c.trial_status()["active"]


def test_a_402_ends_the_trial_and_the_free_models_answer_the_same_decision():
    def no_credit(m, body):
        return (402, {}, {"error": {"message": "Insufficient credits"}}) if m == PV else None
    fake = Fake(reply=no_credit)
    c, _ = client(fake)
    res = ask(c, "vision")
    assert res.ok and res.model == VISION and res.tried == [(PV, "PAID_TRIAL_STOPPED")]
    assert ask(c, "judge", "j").model == TRADER
    assert c.trial_status()["reserved_unconfirmed"] == 0  # a refusal bills nothing


def test_a_paid_seat_served_by_another_model_is_discarded_and_ends_the_trial():
    def swapped(m, body):
        return ok(json.dumps({"x": 1}), "lab-z/pricier-model", cost=0.01) if m == PV else None
    fake = Fake(reply=swapped)
    c, _ = client(fake)
    res = ask(c, "vision")
    assert res.ok and res.model == VISION and res.tried == [(PV, "WRONG_MODEL")]
    assert ask(c, "judge", "j").model == TRADER and "served by" in c.trial_status()["stopped"]


def test_a_free_model_that_reports_a_cost_is_still_discarded_during_the_trial():
    def free_costs(m, body):
        return ok(json.dumps({"x": 1}), m, cost=0.001) if m == VISION else None
    fake = Fake(cat=catalog(pv=paid(PV, prompt="9")), reply=free_costs)  # the paid model priced out: the free one asked
    c, _ = client(fake)
    res = ask(c, "vision")
    assert res.status == "NOT_FREE" and res.model == VISION and PV not in fake.calls
    assert VISION in c.selection()["excluded"]


def test_spend_nobody_accounts_for_still_stops_every_request():
    fake = Fake()
    c, now = client(fake)
    assert ask(c, "vision").model == PV
    now[0] += KEY_CHECK_S + 1
    assert ask(c, "vision", "k2").model == PV  # the key rose by exactly what the paid replies cost: carry on
    fake.extra = 0.50  # something else spent from the key
    now[0] += KEY_CHECK_S + 1
    res = ask(c, "judge", "k3")
    assert res.status == "PAID_USAGE" and c.health()["status"] == "PAID_USAGE_STOPPED"
    n = len(fake.calls)
    assert ask(c, "vision", "k4").status == "PAID_USAGE" and len(fake.calls) == n  # nothing more is sent


# ── the declared trial ───────────────────────────────────────────────────

def test_the_declared_trial_is_the_owners_week_within_the_owners_ten_dollars():
    t = PAID_TRIAL
    assert set(t.models) == {"vision", "judge"} and t.models["vision"].id != t.models["judge"].id
    assert t.models["vision"].id.split("/")[0] != t.models["judge"].id.split("/")[0]  # two different labs
    a, b = t.window()
    assert b - a <= 8 * 86400 and t.ends == "2026-10-31T00:00:00Z"
    assert t.total_usd <= 9.0 and t.daily_usd * 5 <= t.total_usd + 1e-9
    for m in t.models.values():  # a normal call at the declared prices never trips NOT_AS_PRICED
        assert PROMPT_TOKENS_RESERVE * m.max_in_per_m / 1e6 + 12000 * m.max_out_per_m / 1e6 <= t.max_call_usd


@pytest.mark.parametrize("kw", [{"total_usd": 11.0}, {"daily_usd": 2.0, "total_usd": 1.0}, {"max_call_usd": 5.0},
                                {"ends": "2026-10-25T00:00:00Z"}])
def test_a_trial_declared_outside_the_owners_limits_is_refused(kw):
    base = dict(name="x", models={"vision": PaidModel("a/b", 1, 1)}, starts="2026-10-26T00:00:00Z",
                ends="2026-10-31T00:00:00Z", total_usd=1.0, daily_usd=0.5, max_call_usd=0.1)
    with pytest.raises(AssertionError):
        PaidTrial(**{**base, **kw})
    with pytest.raises(AssertionError):  # the debate is never a paid seat
        PaidTrial(**{**base, "models": {"verifier": PaidModel("a/b", 1, 1)}})
