"""The cTrader wire format against bytes from Google's protobuf runtime and cTrader's official definitions
(tests/fixtures/ctrader_golden.json, made by scripts/ctrader_golden.py, which also checked every field of the schema
against the official .proto files)."""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import pytest

from aitrader.broker.ctrader import proto as P

GOLDEN = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "ctrader_golden.json").read_text())


def _py(x):
    if isinstance(x, dict):
        return bytes.fromhex(x["__bytes__"]) if set(x) == {"__bytes__"} else {k: _py(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_py(v) for v in x]
    return x


def test_the_fixture_was_made_from_this_schema_and_the_pinned_definitions():
    # editing the schema without re-checking it against the official definitions fails here
    assert GOLDEN["schema_hash"] == P.schema_hash()
    assert GOLDEN["proto_commit"] == P.PROTO_COMMIT
    assert {e["message"] for e in GOLDEN["examples"]} == set(P.SCHEMA)
    assert GOLDEN["fields_checked"] == sum(len(f) for f in P.SCHEMA.values())
    assert GOLDEN["payload_types_checked"] == len(P.PAYLOAD)


@pytest.mark.parametrize("ex", GOLDEN["examples"], ids=lambda e: e["message"])
def test_encoding_and_decoding_match_googles_runtime(ex):
    fields, raw = _py(ex["fields"]), bytes.fromhex(ex["hex"])
    assert P.encode(ex["message"], fields) == raw
    assert P.decode(ex["message"], raw) == fields


@pytest.mark.parametrize("ex", GOLDEN["full_examples"], ids=lambda e: e["message"])
def test_fields_the_schema_does_not_know_are_skipped(ex):
    # an official message with EVERY field set (holidays, trend bars, advanced take profits...) decodes to exactly
    # the schema's fields
    assert P.decode(ex["message"], bytes.fromhex(ex["hex"])) == _py(ex["expected"])


def test_absent_stays_absent_and_an_explicit_false_is_kept():
    # the demo and swap-free checks depend on this: a missing isLive is not "false"
    without = P.encode("ProtoOACtidTraderAccount", {"ctidTraderAccountId": 7, "traderLogin": 1})
    assert "isLive" not in P.decode("ProtoOACtidTraderAccount", without)
    with_false = P.encode("ProtoOACtidTraderAccount", {"ctidTraderAccountId": 7, "isLive": False})
    assert P.decode("ProtoOACtidTraderAccount", with_false)["isLive"] is False
    assert "swapFree" not in P.decode("ProtoOATrader", P.encode("ProtoOATrader", {"ctidTraderAccountId": 1,
                                                                                    "balance": 0,
                                                                                    "depositAssetId": 1}))


def test_extremes_round_trip():
    f = {"ctidTraderAccountId": -(2 ** 63), "symbolId": 2 ** 63 - 1, "orderType": 1, "tradeSide": 2, "volume": 0,
         "stopLoss": -0.0, "comment": "سلام", "slippageInPoints": -(2 ** 31)}
    assert P.decode("ProtoOANewOrderReq", P.encode("ProtoOANewOrderReq", f)) == f
    assert P.decode("ProtoOASpotEvent", P.encode("ProtoOASpotEvent", {"bid": 2 ** 64 - 1}))["bid"] == 2 ** 64 - 1


@pytest.mark.parametrize("name,fields,needle", [
    ("ProtoOANewOrderReq", {"stopLoss": math.nan}, "finite"),
    ("ProtoOANewOrderReq", {"stopLoss": math.inf}, "finite"),
    ("ProtoOANewOrderReq", {"volume": True}, "integer"),
    ("ProtoOANewOrderReq", {"volume": 1.5}, "integer"),
    ("ProtoOANewOrderReq", {"slippageInPoints": 2 ** 31}, "outside"),
    ("ProtoOASpotEvent", {"bid": -1}, "outside"),
    ("ProtoOACtidTraderAccount", {"isLive": 0}, "bool"),
    ("ProtoOANewOrderReq", {"stopLos": 1.0}, "unknown fields"),  # a typo must not silently drop a stop
    ("ProtoOASymbolByIdReq", {"symbolId": 5}, "list"),
    ("ProtoOAReconcileRes", {"position": [5]}, "dict"),
    ("NoSuchMessage", {}, "unknown message"),
])
def test_values_that_cannot_be_sent_are_refused(name, fields, needle):
    with pytest.raises(P.ProtoError, match=needle):
        P.encode(name, fields)


@pytest.mark.parametrize("raw,needle", [
    (b"\x08", "truncated varint"),
    (b"\x08" + b"\xff" * 10 + b"\x01", "ten bytes"),
    (b"\x12\x05ab", "truncated"),  # a string announced longer than the bytes
    (b"\x10\x01", "wire type 0, expected 2"),  # clientId (a string) arriving as a varint
    (b"\x00\x01", "field number 0"),
    (b"\x0b", "wire type 3"),  # groups are not supported
])
def test_malformed_bytes_raise(raw, needle):
    with pytest.raises(P.ProtoError, match=needle):
        P.decode("ProtoOAApplicationAuthReq", raw)


def test_a_wire_type_that_contradicts_the_schema_raises():
    # isLive is field 2 (bool, varint); bytes arriving as length-delimited for it are refused, not guessed
    with pytest.raises(P.ProtoError, match="wire type 2"):
        P.decode("ProtoOACtidTraderAccount", b"\x12\x01\x01")


def test_a_packed_repeated_scalar_is_accepted():
    # proto2 sends repeated scalars unpacked, and parsers must accept the packed form too (hand-built bytes:
    # field 3, wire type 2, three varints 1, 300, 2)
    raw = b"\x1a\x04\x01\xac\x02\x02"
    assert P.decode("ProtoOASymbolByIdReq", raw)["symbolId"] == [1, 300, 2]


def test_the_envelope_leaves_the_inner_payload_type_out_and_round_trips():
    env = P.envelope("ProtoOATraderReq", {"ctidTraderAccountId": 9}, "c1")
    pt, payload, cid = P.open_envelope(env)
    assert (pt, cid) == (2121, "c1")
    assert payload == P.encode("ProtoOATraderReq", {"ctidTraderAccountId": 9})
    with pytest.raises(P.ProtoError, match="payloadType"):
        P.open_envelope(P.encode("ProtoMessage", {"clientMsgId": "x"}))
    with pytest.raises(P.ProtoError, match="top-level"):
        P.envelope("ProtoOATrader", {})


def test_frames_carry_their_length_and_have_a_limit():
    assert P.frame(b"abc") == struct.pack(">I", 3) + b"abc"
    with pytest.raises(P.ProtoError, match="over the limit"):
        P.frame(b"\x00" * (P.MAX_FRAME + 1))
