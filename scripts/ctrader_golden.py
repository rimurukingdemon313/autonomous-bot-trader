"""Checks aitrader/broker/ctrader/proto.py against cTrader's official message definitions, and writes the golden bytes
its tests compare with (tests/fixtures/ctrader_golden.json). Not part of the test suite: it needs Google's protobuf
runtime and the classes generated from Spotware's .proto files, which the suite does not install.

    git clone https://github.com/spotware/openapi-proto-messages P            # at proto.PROTO_COMMIT
    pip install protobuf grpcio-tools
    python -m grpc_tools.protoc -I P --python_out=G P/*.proto
    python scripts/ctrader_golden.py --pb G [--out tests/fixtures/ctrader_golden.json]

It fails, writing nothing, if any field of the schema differs from the official one in name, number, type or
repetition, if a payload type differs, or if an enum value used differs.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from aitrader.broker.ctrader import proto as P  # noqa: E402

MODULES = ("OpenApiCommonModelMessages_pb2", "OpenApiCommonMessages_pb2", "OpenApiModelMessages_pb2",
           "OpenApiMessages_pb2")
#: messages whose official definition has fields this schema leaves out: a fully populated official message must
#: decode to exactly the schema's fields
FULL = ("ProtoOASymbol", "ProtoOASymbolsListRes", "ProtoOASpotEvent", "ProtoOAPosition", "ProtoOAOrder",
        "ProtoOAExecutionEvent", "ProtoOATrader", "ProtoOANewOrderReq", "ProtoOAAmendPositionSLTPReq")


def official(mods, name):
    for m in mods:
        if hasattr(m, name):
            return getattr(m, name)
    raise SystemExit(f"{name} is not in the official definitions")


def type_name(fd) -> str:
    from google.protobuf.descriptor import FieldDescriptor as F
    names = {F.TYPE_INT64: "int64", F.TYPE_UINT64: "uint64", F.TYPE_INT32: "int32", F.TYPE_UINT32: "uint32",
             F.TYPE_BOOL: "bool", F.TYPE_ENUM: "enum", F.TYPE_DOUBLE: "double", F.TYPE_STRING: "string",
             F.TYPE_BYTES: "bytes"}
    return fd.message_type.name if fd.type == F.TYPE_MESSAGE else names.get(fd.type, f"type{fd.type}")


def is_repeated(fd) -> bool:
    rep = getattr(fd, "is_repeated", None)
    return bool(rep) if rep is not None else fd.label == fd.LABEL_REPEATED


def check_schema(mods) -> tuple[int, int]:
    problems, fields, payloads = [], 0, 0
    for name, schema in P.SCHEMA.items():
        desc = official(mods, name).DESCRIPTOR
        for fname, (num, typ, rep) in schema.items():
            fd = desc.fields_by_name.get(fname)
            fields += 1
            if fd is None:
                problems.append(f"{name}.{fname}: not in the official definition")
                continue
            got = (fd.number, type_name(fd), is_repeated(fd))
            if got != (num, typ, rep):
                problems.append(f"{name}.{fname}: schema {(num, typ, rep)}, official {got}")
        if name in P.PAYLOAD:
            payloads += 1
            pt = desc.fields_by_name.get("payloadType")
            if pt is None or pt.default_value != P.PAYLOAD[name]:
                problems.append(f"{name}: payload type {P.PAYLOAD[name]}, official "
                                f"{pt.default_value if pt else 'none'}")
    for enum, ours in (("ProtoOATradeSide", P.TRADE_SIDE), ("ProtoOAOrderType", P.ORDER_TYPE)):
        e = official(mods, enum)
        for k, v in ours.items():
            if e.Value(k) != v:
                problems.append(f"{enum}.{k}: {v}, official {e.Value(k)}")
    for enum, ours in (("ProtoOAExecutionType", P.EXECUTION_TYPE), ("ProtoOAAccountType", P.ACCOUNT_TYPE),
                       ("ProtoOAAccessRights", P.ACCESS_RIGHTS), ("ProtoOATradingMode", P.TRADING_MODE),
                       ("ProtoOASwapCalculationType", P.SWAP_CALCULATION)):
        e = official(mods, enum)
        for v, k in ours.items():
            if e.Value(k) != v:
                problems.append(f"{enum}.{k}: {v}, official {e.Value(k)}")
    if problems:
        raise SystemExit("the schema differs from the official definitions:\n" + "\n".join(problems))
    return fields, payloads


def value(fd, k: int, mods):
    """A deterministic value for one field: negative and ten-byte integers, numbers past int64, explicit false,
    non-ASCII text, nested and repeated messages."""
    t, n = type_name(fd), fd.number
    if t == "int64":
        return -(2 ** 40 + n * 7 + k) if (n + k) % 2 else 2 ** 50 + n + k
    if t == "uint64":
        return 2 ** 63 + n + k
    if t == "int32":
        return -(n * 1000 + k) if (n + k) % 2 else n * 1000 + k
    if t == "uint32":
        return 2 ** 32 - 1 - n - k
    if t == "bool":
        return (n + k) % 2 == 1
    if t == "enum":
        vals = fd.enum_type.values
        return vals[(n + k) % len(vals)].number
    if t == "double":
        return (n + k) * 1.0000001 + 0.123456789 if (n + k) % 2 else -(n + k) * 0.5 - 0.25
    if t == "string":
        return f"f{n}-{k}-é€"
    if t == "bytes":
        return bytes([0, 1, 255, n % 256, k % 256]) + b"payload"
    raise AssertionError(t)


def populate(msg, mods, names: set[str] | None, depth: int = 0):
    """Set the fields named in `names` (the schema's), or every field when names is None, recursively."""
    for fd in msg.DESCRIPTOR.fields:
        if names is not None and fd.name not in names:
            continue
        if fd.name == "payloadType":
            continue  # left out, as the official clients leave it
        sub = P.SCHEMA.get(fd.message_type.name) if fd.message_type is not None else None
        if fd.message_type is not None:
            if depth > 3:
                continue
            subnames = set(sub) if (sub is not None and names is not None) else None
            if names is not None and sub is None:
                continue
            if is_repeated(fd):
                for _ in range(2):
                    populate(getattr(msg, fd.name).add(), mods, subnames, depth + 1)
            else:
                populate(getattr(msg, fd.name), mods, subnames, depth + 1)
        elif is_repeated(fd):
            getattr(msg, fd.name).extend([value(fd, k, mods) for k in range(3)])
        else:
            setattr(msg, fd.name, value(fd, 0, mods))
    return msg


def restrict(msg, name: str) -> dict:
    """What the schema's decoder must return for an official message: its schema fields that are present."""
    out = {}
    for fname, (num, typ, rep) in P.SCHEMA[name].items():
        if rep:
            vals = list(getattr(msg, fname))
            if vals:
                out[fname] = [restrict(v, typ) for v in vals] if typ in P.SCHEMA else vals
        elif msg.HasField(fname):
            v = getattr(msg, fname)
            out[fname] = restrict(v, typ) if typ in P.SCHEMA else v
    return out


def jsonable(x):
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, list):
        return [jsonable(v) for v in x]
    if isinstance(x, bytes):
        return {"__bytes__": x.hex()}
    return x


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pb", required=True, type=Path, help="the directory of the generated *_pb2.py modules")
    ap.add_argument("--out", type=Path, default=ROOT / "tests" / "fixtures" / "ctrader_golden.json")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(a.pb.resolve()))
    import google.protobuf
    mods = [importlib.import_module(m) for m in MODULES]
    fields, payloads = check_schema(mods)
    examples, full = [], []
    for name in P.SCHEMA:
        msg = populate(official(mods, name)(), mods, set(P.SCHEMA[name]))
        raw = msg.SerializePartialToString()
        examples.append({"message": name, "fields": jsonable(restrict(msg, name)), "hex": raw.hex()})
    for name in FULL:
        msg = populate(official(mods, name)(), mods, None)
        raw = msg.SerializePartialToString()
        full.append({"message": name, "expected": jsonable(restrict(msg, name)), "hex": raw.hex()})
    body = {"about": "golden bytes from Google's protobuf runtime and cTrader's official definitions; made by "
                     "scripts/ctrader_golden.py", "proto_commit": P.PROTO_COMMIT, "schema_hash": P.schema_hash(),
            "protobuf_runtime": google.protobuf.__version__, "fields_checked": fields,
            "payload_types_checked": payloads, "examples": examples, "full_examples": full}
    a.out.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
    print(f"schema checked: {len(P.SCHEMA)} messages, {fields} fields, {payloads} payload types; "
          f"{len(examples)} examples, {len(full)} full examples -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
