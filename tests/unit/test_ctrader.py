"""The cTrader demo connection and its probe, against a fake proxy at the socket (tests/ctrader_kit.py): the demo
and swap-free checks from the broker's own records, nothing asked of a refused account, no order ever sent, no
secret or account number in a report, and prices measured exactly as built."""

from __future__ import annotations

import json
import socket
import struct
import time
from datetime import datetime, timezone

import pytest

from aitrader.broker.ctrader import proto as P
from aitrader.broker.ctrader.client import ApiError, CallTimeout, Client, ConnectionLost, ProtocolError
from aitrader.broker.ctrader.guard import verify_demo, verify_swap_free
from aitrader.broker.ctrader.session import Credentials, open_session, scrub
from aitrader.broker.ctrader.transport import DEMO_HOST, LIVE_HOST, PORT, DemoRefused, Transport, TransportError
from scripts import ctrader_probe as probe_mod
from tests.ctrader_kit import CTID, LOGIN, WRITES, FakeCTrader, demo_account, env, spot, trader

NOW = datetime(2026, 11, 16, 14, 0, tzinfo=timezone.utc)
CREDS, _ = Credentials.from_env(env())


@pytest.fixture
def fakes():
    made = []

    def make(**kw):
        f = FakeCTrader(**kw)
        made.append(f)
        return f
    yield make
    for f in made:
        f.close()


def client_for(fake, **kw) -> Client:
    return Client(Transport(connect=fake.connect), **kw)


# ── the host ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("host", [LIVE_HOST, "demo.ctraderapi.com.example.net", "DEMO.ctraderapi.com", ""])
def test_any_host_but_the_demo_proxy_is_refused_before_connecting(host):
    calls = []
    with pytest.raises(DemoRefused, match="refused"):
        Transport(host=host, connect=lambda *a: calls.append(a))
    assert calls == []


def test_the_demo_proxy_is_the_default_and_the_only_host(fakes):
    f = fakes()
    Transport(connect=f.connect)
    assert f.connected_to == (DEMO_HOST, PORT) == ("demo.ctraderapi.com", 5035)


# ── the demo check (CLAUDE.md rule 1) ───────────────────────────────────────

@pytest.mark.parametrize("acct,needle", [
    (demo_account(isLive=True), "LIVE"),
    ({k: v for k, v in demo_account().items() if k != "isLive"}, "no isLive field"),
    (demo_account(traderLogin=LOGIN + 1), "none has the configured login"),
])
def test_the_probe_refuses_an_account_the_broker_does_not_mark_demo_and_asks_it_nothing_more(fakes, tmp_path, acct,
                                                                                              needle):
    f = fakes(accounts=[acct])
    rc = probe_mod.main(["--minutes", "0", "--out", str(tmp_path)], env=env(), connect=f.connect)
    rep = json.loads((tmp_path / "probe.json").read_text())
    assert rc == 1 and rep["status"] == "REFUSED" and needle in rep["demo"]["why"]
    assert "Fields read: connection host, ctidTraderAccount[].traderLogin, ctidTraderAccount[].isLive" in \
        rep["demo"]["why"]  # the failure names the fields it looked at
    # nothing was asked of the account after the check failed: it was never authorised
    assert f.names() == ["ProtoOAApplicationAuthReq", "ProtoOAGetAccountListByAccessTokenReq"]


def test_two_listed_accounts_with_the_configured_login_are_ambiguous_and_refused():
    v = verify_demo(DEMO_HOST, [demo_account(), demo_account(ctidTraderAccountId=CTID + 1)], LOGIN)
    assert not v.ok and "cannot be told" in v.why


def test_the_demo_check_needs_both_signals():
    assert verify_demo(DEMO_HOST, [demo_account()], LOGIN).ok
    assert verify_demo(DEMO_HOST, [demo_account()], LOGIN).account_id == CTID
    assert not verify_demo(LIVE_HOST, [demo_account()], LOGIN).ok  # the broker's demo flag alone is not enough
    assert not verify_demo(DEMO_HOST, [demo_account(isLive=None)], LOGIN).ok
    assert not verify_demo(DEMO_HOST, [demo_account(isLive=0)], LOGIN).ok  # only an explicit false passes
    assert not verify_demo(DEMO_HOST, [], LOGIN).ok


def test_an_account_record_that_is_not_the_checked_account_is_refused(fakes):
    f = fakes(trader_rec=trader(traderLogin=LOGIN + 5))
    with pytest.raises(DemoRefused, match="not the account that passed the demo check"):
        open_session(client_for(f), CREDS)


# ── the swap-free check (the owner's condition) ─────────────────────────────

def test_swap_free_only_on_the_brokers_explicit_word():
    assert verify_swap_free({"swapFree": True}).ok
    assert not verify_swap_free({}).ok and "no swapFree field" in verify_swap_free({}).why
    assert not verify_swap_free({"swapFree": False}).ok and "NOT swap-free" in verify_swap_free({"swapFree": False}).why
    assert not verify_swap_free({"swapFree": 1}).ok


def test_a_demo_account_that_is_not_swap_free_is_reported_as_unusable_for_orders(fakes, tmp_path):
    f = fakes(trader_rec={k: v for k, v in trader().items() if k != "swapFree"})
    rc = probe_mod.main(["--minutes", "0", "--out", str(tmp_path)], env=env(), connect=f.connect)
    rep = json.loads((tmp_path / "probe.json").read_text())
    assert rc == 0 and rep["status"] == "DONE" and rep["demo"]["ok"] is True
    assert rep["swap_free"]["ok"] is False and "not used for orders" in rep["swap_free"]["why"]
    assert "ما ينفتح عليه أي أمر" in (tmp_path / "REPORT.md").read_text()


# ── the probe ───────────────────────────────────────────────────────────────

def test_the_probe_measures_what_was_built_and_sends_no_order(fakes, tmp_path):
    f = fakes(spots_before=[spot(101, 5000.0, 5000.5)],  # arrives before the subscription's answer
              spots=[spot(101, ask=5000.7),  # one side only: the other side's last value stands
                     spot(101, bid=5000.2),
                     spot(102, bid=20000.0),  # NAS100: no ask yet, so no spread yet
                     spot(102, ask=20001.5),
                     spot(999, 1.0, 2.0)])  # a symbol not asked for is ignored
    rc = probe_mod.main(["--minutes", "0.01", "--out", str(tmp_path)], env=env(), connect=f.connect)
    rep = json.loads((tmp_path / "probe.json").read_text())
    assert rc == 0 and rep["status"] == "DONE" and rep["orders_placed"] == 0
    assert not any(n in WRITES for n in f.names())  # no order, stop move or close was ever sent
    assert rep["demo"]["ok"] and rep["swap_free"]["ok"]
    us = rep["spreads"]["US500"]
    assert us["quotes"] == 3 and us["median"] == 0.5 and us["max"] == 0.7 and us["assumed"] == 0.5
    assert rep["spreads"]["NAS100"]["quotes"] == 1 and rep["spreads"]["NAS100"]["median"] == 1.5
    ger = rep["spreads"]["GER40"]
    assert ger["quotes"] == 0 and ger["median"] is None  # no quotes is a visible gap, never a zero spread
    assert rep["missing"] == ["UK100"]
    assert [x["name"] for x in rep["desk_symbols"]["US500"]] == ["US500.cash"]  # not the future "US500.f"
    assert rep["desk_symbols"]["US500"][0]["swapCalculationType"] == "PERCENTAGE"
    assert rep["desk_symbols"]["US500"][0]["open_hours_a_week"] == 23.0
    a = rep["account"]
    assert a["balance"] == 200000.0 and a["deposit_currency"] == "USD" and a["leverage"] == 30.0
    assert a["token_scope"] == "SCOPE_TRADE" and a["account_type"] == "HEDGED"
    assert f.names()[-1] == "ProtoOAAccountLogoutReq"


def test_no_secret_and_no_account_number_reaches_a_report(fakes, tmp_path):
    token = env()["CTRADER_ACCESS_TOKEN"]
    f = fakes(errors={"ProtoOAAccountAuthReq": ("CH_ACCESS_TOKEN_INVALID", f"token {token} is invalid")})
    rc = probe_mod.main(["--minutes", "0", "--out", str(tmp_path)], env=env(), connect=f.connect)
    rep = json.loads((tmp_path / "probe.json").read_text())
    assert rc == 1 and rep["status"] == "ERROR" and "CH_ACCESS_TOKEN_INVALID" in rep["error"]
    assert "replace CTRADER_ACCESS_TOKEN" in rep["error"]  # the operator is told what to do
    for p in (tmp_path / "probe.json", tmp_path / "REPORT.md"):
        text = p.read_text()
        for secret in list(env().values()) + [str(CTID)]:
            assert secret not in text
    # a successful probe names no account number either
    f2 = fakes()
    out = tmp_path / "ok"
    assert probe_mod.main(["--minutes", "0", "--out", str(out)], env=env(), connect=f2.connect) == 0
    for p in (out / "probe.json", out / "REPORT.md"):
        assert str(LOGIN) not in p.read_text() and str(CTID) not in p.read_text()


def test_missing_settings_are_named_and_nothing_connects(tmp_path):
    calls = []
    rc = probe_mod.main(["--minutes", "0", "--out", str(tmp_path)],
                        env=env(CTRADER_ACCESS_TOKEN=None, CTRADER_CLIENT_SECRET="  "),
                        connect=lambda *a: calls.append(a))
    rep = json.loads((tmp_path / "probe.json").read_text())
    assert rc == 1 and rep["status"] == "NOT_CONFIGURED" and calls == []
    assert rep["missing_settings"] == ["CTRADER_CLIENT_SECRET", "CTRADER_ACCESS_TOKEN"]
    assert Credentials.from_env(env(CTRADER_ACCOUNT_LOGIN="12a"))[1] == [
        "CTRADER_ACCOUNT_LOGIN (must be the account's number)"]
    assert "hidden" in repr(CREDS) and "access-token" not in repr(CREDS)


def test_scrub_replaces_every_secret_longest_first():
    assert scrub("a abcdef abcd xyz", ("abcd", "abcdef", "xy")) == "a [hidden] [hidden] xyz"


# ── the connection ──────────────────────────────────────────────────────────

def test_frames_split_into_single_bytes_are_reassembled(fakes):
    f = fakes(chunk=1)
    s = open_session(client_for(f), CREDS)
    assert s.account_id == CTID and s.demo.ok and s.swap_free.ok


def test_a_frame_cut_by_a_timeout_is_completed_by_the_next_read():
    a, b = socket.socketpair()
    try:
        t = Transport(connect=lambda *x: a)
        data = P.frame(P.envelope("ProtoOAVersionRes", {"version": "99"}, "c1"))
        b.sendall(data[:5])
        assert t.recv(0.05) is None
        b.sendall(data[5:])
        assert P.open_envelope(t.recv(1.0))[2] == "c1"
    finally:
        a.close()
        b.close()


def test_an_oversized_frame_is_refused_and_a_closed_connection_says_so():
    a, b = socket.socketpair()
    try:
        t = Transport(connect=lambda *x: a)
        b.sendall(struct.pack(">I", P.MAX_FRAME + 1))
        with pytest.raises(TransportError, match="announced a frame"):
            t.recv(1.0)
        with pytest.raises(TransportError, match="closed"):
            t.send(b"x")
    finally:
        b.close()
    a2, b2 = socket.socketpair()
    t2 = Transport(connect=lambda *x: a2)
    b2.close()
    with pytest.raises(TransportError, match="closed the connection"):
        t2.recv(1.0)


def test_errors_timeouts_wrong_answers_and_disconnects_are_typed(fakes):
    f = fakes(errors={"ProtoOAApplicationAuthReq": ("CH_CLIENT_AUTH_FAILURE", "")})
    with pytest.raises(ApiError, match="not activated yet"):
        open_session(client_for(f), CREDS)
    f = fakes(silent={"ProtoOATraderReq"})
    c = client_for(f)
    with pytest.raises(CallTimeout):
        c.call("ProtoOATraderReq", {"ctidTraderAccountId": CTID}, ("ProtoOATraderRes",), timeout=0.2)
    f = fakes(answer_with={"ProtoOATraderReq": ("ProtoOAAssetListRes", {"ctidTraderAccountId": CTID})})
    with pytest.raises(ProtocolError, match="answered with ProtoOAAssetListRes"):
        client_for(f).call("ProtoOATraderReq", {"ctidTraderAccountId": CTID}, ("ProtoOATraderRes",), timeout=2)
    f = fakes(disconnect_on="ProtoOAAccountAuthReq")
    c = client_for(f)
    with pytest.raises(ConnectionLost, match="blocked by the administrator"):
        open_session(c, CREDS)
    assert c.transport.closed


def test_heartbeats_keep_an_idle_connection_open(fakes):
    f = fakes()
    c = client_for(f, heartbeat_every=0.05)
    c.pump(0.35)
    time.sleep(0.05)
    assert f.heartbeats >= 3


def test_an_answer_is_matched_by_its_clientMsgId_and_the_others_are_kept():
    a, b = socket.socketpair()
    try:
        c = Client(Transport(connect=lambda *x: a))
        # an answer carrying another request's id arrives first: it is kept as an event, never taken as this answer
        b.sendall(P.frame(P.envelope("ProtoOATraderRes", {"ctidTraderAccountId": 1, "trader": trader(balance=1)},
                                     "zz")))
        b.sendall(P.frame(P.envelope("ProtoOATraderRes", {"ctidTraderAccountId": 1, "trader": trader(balance=2)},
                                     "c1")))
        name, msg = c.call("ProtoOATraderReq", {"ctidTraderAccountId": 1}, ("ProtoOATraderRes",), timeout=2)
        assert msg["trader"]["balance"] == 2
        assert [e[2] for e in c.events] == ["zz"]
    finally:
        a.close()
        b.close()
