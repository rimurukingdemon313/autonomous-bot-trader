"""The cTrader Open API's wire format (docs/CTRADER.md).

Every message is protobuf 2 inside a ProtoMessage envelope, and each envelope travels over TLS prefixed by its length
(4 bytes, big-endian). Only the messages this system uses are described below, with the field numbers and types of
Spotware's own definitions (github.com/spotware/openapi-proto-messages, commit PROTO_COMMIT).

The codec is checked against bytes that Google's protobuf runtime produced from those definitions, and the schema is
checked field by field against the same definitions (tests/fixtures/ctrader_golden.json, made by
scripts/ctrader_golden.py). A wrong field number or type therefore fails a test, not a request to a broker.

An optional field the broker left out is ABSENT from a decoded dict, never filled with its default. The demo and
swap-free checks depend on it: absence of evidence fails (CLAUDE.md rule 1).
"""

from __future__ import annotations

import hashlib
import math
import struct

PROTO_COMMIT = "a9676f27f40b60569fb8a510aeadedba901b74e9"  # spotware/openapi-proto-messages, 2026-11-04
MAX_FRAME = 4 * 1024 * 1024  # a frame announcing more than this is refused before it is read


class ProtoError(ValueError):
    """Bytes that are not the message they claim to be, or a value that cannot be encoded."""


# name: field=number type[*]; ...   (* = repeated; a type starting with "Proto" is a message)
_SPEC = """
ProtoMessage: payloadType=1 uint32; payload=2 bytes; clientMsgId=3 string
ProtoErrorRes: errorCode=2 string; description=3 string; maintenanceEndTimestamp=4 uint64
ProtoHeartbeatEvent:
ProtoOAApplicationAuthReq: clientId=2 string; clientSecret=3 string
ProtoOAApplicationAuthRes:
ProtoOAAccountAuthReq: ctidTraderAccountId=2 int64; accessToken=3 string
ProtoOAAccountAuthRes: ctidTraderAccountId=2 int64
ProtoOAAccountLogoutReq: ctidTraderAccountId=2 int64
ProtoOAAccountLogoutRes: ctidTraderAccountId=2 int64
ProtoOAVersionReq:
ProtoOAVersionRes: version=2 string
ProtoOAGetAccountListByAccessTokenReq: accessToken=2 string
ProtoOAGetAccountListByAccessTokenRes: accessToken=2 string; permissionScope=3 enum; ctidTraderAccount=4 ProtoOACtidTraderAccount*
ProtoOACtidTraderAccount: ctidTraderAccountId=1 uint64; isLive=2 bool; traderLogin=3 int64; lastClosingDealTimestamp=4 int64; lastBalanceUpdateTimestamp=5 int64; brokerTitleShort=6 string
ProtoOATraderReq: ctidTraderAccountId=2 int64
ProtoOATraderRes: ctidTraderAccountId=2 int64; trader=3 ProtoOATrader
ProtoOATrader: ctidTraderAccountId=1 int64; balance=2 int64; balanceVersion=3 int64; managerBonus=4 int64; ibBonus=5 int64; nonWithdrawableBonus=6 int64; accessRights=7 enum; depositAssetId=8 int64; swapFree=9 bool; leverageInCents=10 uint32; totalMarginCalculationType=11 enum; maxLeverage=12 uint32; frenchRisk=13 bool; traderLogin=14 int64; accountType=15 enum; brokerName=16 string; registrationTimestamp=17 int64; isLimitedRisk=18 bool; limitedRiskMarginCalculationStrategy=19 enum; moneyDigits=20 uint32; fairStopOut=21 bool; stopOutStrategy=22 enum; accountLifetimeType=23 enum
ProtoOAErrorRes: ctidTraderAccountId=2 int64; errorCode=3 string; description=4 string; maintenanceEndTimestamp=5 int64; retryAfter=6 uint64
ProtoOARefreshTokenReq: refreshToken=2 string
ProtoOARefreshTokenRes: accessToken=2 string; tokenType=3 string; expiresIn=4 int64; refreshToken=5 string
ProtoOAReconcileReq: ctidTraderAccountId=2 int64; returnProtectionOrders=3 bool
ProtoOAReconcileRes: ctidTraderAccountId=2 int64; position=3 ProtoOAPosition*; order=4 ProtoOAOrder*
ProtoOAPosition: positionId=1 int64; tradeData=2 ProtoOATradeData; positionStatus=3 enum; swap=4 int64; price=5 double; stopLoss=6 double; takeProfit=7 double; utcLastUpdateTimestamp=8 int64; commission=9 int64; marginRate=10 double; mirroringCommission=11 int64; guaranteedStopLoss=12 bool; usedMargin=13 uint64; stopLossTriggerMethod=14 enum; moneyDigits=15 uint32; trailingStopLoss=16 bool
ProtoOATradeData: symbolId=1 int64; volume=2 int64; tradeSide=3 enum; openTimestamp=4 int64; label=5 string; guaranteedStopLoss=6 bool; comment=7 string; measurementUnits=8 string; closeTimestamp=9 uint64
ProtoOAOrder: orderId=1 int64; tradeData=2 ProtoOATradeData; orderType=3 enum; orderStatus=4 enum; expirationTimestamp=6 int64; executionPrice=7 double; executedVolume=8 int64; utcLastUpdateTimestamp=9 int64; baseSlippagePrice=10 double; slippageInPoints=11 int64; closingOrder=12 bool; limitPrice=13 double; stopPrice=14 double; stopLoss=15 double; takeProfit=16 double; clientOrderId=17 string; timeInForce=18 enum; positionId=19 int64; relativeStopLoss=20 int64; relativeTakeProfit=21 int64; isStopOut=22 bool; trailingStopLoss=23 bool; stopTriggerMethod=24 enum
ProtoOADeal: dealId=1 int64; orderId=2 int64; positionId=3 int64; volume=4 int64; filledVolume=5 int64; symbolId=6 int64; createTimestamp=7 int64; executionTimestamp=8 int64; utcLastUpdateTimestamp=9 int64; executionPrice=10 double; tradeSide=11 enum; dealStatus=12 enum; marginRate=13 double; commission=14 int64; baseToUsdConversionRate=15 double; closePositionDetail=16 ProtoOAClosePositionDetail; moneyDigits=17 uint32; label=18 string; comment=19 string; rejectReason=20 string
ProtoOAClosePositionDetail: entryPrice=1 double; grossProfit=2 int64; swap=3 int64; commission=4 int64; balance=5 int64; quoteToDepositConversionRate=6 double; closedVolume=7 int64; balanceVersion=8 int64; moneyDigits=9 uint32; pnlConversionFee=10 int64
ProtoOAGetPositionUnrealizedPnLReq: ctidTraderAccountId=2 int64
ProtoOAGetPositionUnrealizedPnLRes: ctidTraderAccountId=2 int64; positionUnrealizedPnL=3 ProtoOAPositionUnrealizedPnL*; moneyDigits=4 uint32
ProtoOAPositionUnrealizedPnL: positionId=1 int64; grossUnrealizedPnL=2 int64; netUnrealizedPnL=3 int64
ProtoOAAssetListReq: ctidTraderAccountId=2 int64
ProtoOAAssetListRes: ctidTraderAccountId=2 int64; asset=3 ProtoOAAsset*
ProtoOAAsset: assetId=1 int64; name=2 string; displayName=3 string; digits=4 int32
ProtoOASymbolsListReq: ctidTraderAccountId=2 int64; includeArchivedSymbols=3 bool
ProtoOASymbolsListRes: ctidTraderAccountId=2 int64; symbol=3 ProtoOALightSymbol*
ProtoOALightSymbol: symbolId=1 int64; symbolName=2 string; enabled=3 bool; baseAssetId=4 int64; quoteAssetId=5 int64; symbolCategoryId=6 int64; description=7 string; sortingNumber=8 double
ProtoOASymbolByIdReq: ctidTraderAccountId=2 int64; symbolId=3 int64*
ProtoOASymbolByIdRes: ctidTraderAccountId=2 int64; symbol=3 ProtoOASymbol*
ProtoOASymbol: symbolId=1 int64; digits=2 int32; pipPosition=3 int32; enableShortSelling=4 bool; guaranteedStopLoss=5 bool; swapRollover3Days=6 enum; swapLong=7 double; swapShort=8 double; maxVolume=9 int64; minVolume=10 int64; stepVolume=11 int64; maxExposure=12 uint64; schedule=13 ProtoOAInterval*; commission=14 int64; commissionType=15 enum; slDistance=16 uint32; tpDistance=17 uint32; gslDistance=18 uint32; gslCharge=19 int64; distanceSetIn=20 enum; minCommission=21 int64; minCommissionType=22 enum; minCommissionAsset=23 string; rolloverCommission=24 int64; skipRolloverDays=25 int32; scheduleTimeZone=26 string; tradingMode=27 enum; rolloverCommission3Days=28 enum; swapCalculationType=29 enum; lotSize=30 int64; preciseTradingCommissionRate=31 int64; preciseMinCommission=32 int64; pnlConversionFeeRate=34 int32; leverageId=35 int64; swapPeriod=36 int32; swapTime=37 int32; skipSWAPPeriods=38 int32; chargeSwapAtWeekends=39 bool; measurementUnits=40 string; gslScheduleId=41 uint64
ProtoOAInterval: startSecond=3 uint32; endSecond=4 uint32
ProtoOASubscribeSpotsReq: ctidTraderAccountId=2 int64; symbolId=3 int64*; subscribeToSpotTimestamp=4 bool
ProtoOASubscribeSpotsRes: ctidTraderAccountId=2 int64; subscribedSymbolId=3 int64*
ProtoOAUnsubscribeSpotsReq: ctidTraderAccountId=2 int64; symbolId=3 int64*
ProtoOAUnsubscribeSpotsRes: ctidTraderAccountId=2 int64
ProtoOASpotEvent: ctidTraderAccountId=2 int64; symbolId=3 int64; bid=4 uint64; ask=5 uint64; sessionClose=7 uint64; timestamp=8 int64
ProtoOADealListReq: ctidTraderAccountId=2 int64; fromTimestamp=3 int64; toTimestamp=4 int64; maxRows=5 int32
ProtoOADealListRes: ctidTraderAccountId=2 int64; deal=3 ProtoOADeal*; hasMore=4 bool
ProtoOANewOrderReq: ctidTraderAccountId=2 int64; symbolId=3 int64; orderType=4 enum; tradeSide=5 enum; volume=6 int64; limitPrice=7 double; stopPrice=8 double; timeInForce=9 enum; expirationTimestamp=10 int64; stopLoss=11 double; takeProfit=12 double; comment=13 string; baseSlippagePrice=14 double; slippageInPoints=15 int32; label=16 string; positionId=17 int64; clientOrderId=18 string; relativeStopLoss=19 int64; relativeTakeProfit=20 int64; guaranteedStopLoss=21 bool; trailingStopLoss=22 bool; stopTriggerMethod=23 enum
ProtoOAExecutionEvent: ctidTraderAccountId=2 int64; executionType=3 enum; position=4 ProtoOAPosition; order=5 ProtoOAOrder; deal=6 ProtoOADeal; errorCode=9 string; isServerEvent=10 bool
ProtoOAOrderErrorEvent: errorCode=2 string; orderId=3 int64; ctidTraderAccountId=5 int64; positionId=6 int64; description=7 string
ProtoOAAmendPositionSLTPReq: ctidTraderAccountId=2 int64; positionId=3 int64; stopLoss=4 double; takeProfit=5 double; guaranteedStopLoss=7 bool; trailingStopLoss=8 bool; stopLossTriggerMethod=9 enum
ProtoOAClosePositionReq: ctidTraderAccountId=2 int64; positionId=3 int64; volume=4 int64
ProtoOAAccountsTokenInvalidatedEvent: ctidTraderAccountIds=2 int64*; reason=3 string
ProtoOAClientDisconnectEvent: reason=2 string
ProtoOAAccountDisconnectEvent: ctidTraderAccountId=2 int64
"""

#: payloadType of every top-level message used (the official ProtoPayloadType / ProtoOAPayloadType values)
PAYLOAD = {
    "ProtoErrorRes": 50, "ProtoHeartbeatEvent": 51,
    "ProtoOAApplicationAuthReq": 2100, "ProtoOAApplicationAuthRes": 2101,
    "ProtoOAAccountAuthReq": 2102, "ProtoOAAccountAuthRes": 2103,
    "ProtoOAVersionReq": 2104, "ProtoOAVersionRes": 2105,
    "ProtoOANewOrderReq": 2106, "ProtoOAAmendPositionSLTPReq": 2110, "ProtoOAClosePositionReq": 2111,
    "ProtoOAAssetListReq": 2112, "ProtoOAAssetListRes": 2113,
    "ProtoOASymbolsListReq": 2114, "ProtoOASymbolsListRes": 2115,
    "ProtoOASymbolByIdReq": 2116, "ProtoOASymbolByIdRes": 2117,
    "ProtoOATraderReq": 2121, "ProtoOATraderRes": 2122,
    "ProtoOAReconcileReq": 2124, "ProtoOAReconcileRes": 2125, "ProtoOAExecutionEvent": 2126,
    "ProtoOASubscribeSpotsReq": 2127, "ProtoOASubscribeSpotsRes": 2128,
    "ProtoOAUnsubscribeSpotsReq": 2129, "ProtoOAUnsubscribeSpotsRes": 2130,
    "ProtoOASpotEvent": 2131, "ProtoOAOrderErrorEvent": 2132,
    "ProtoOADealListReq": 2133, "ProtoOADealListRes": 2134, "ProtoOAErrorRes": 2142,
    "ProtoOAAccountsTokenInvalidatedEvent": 2147, "ProtoOAClientDisconnectEvent": 2148,
    "ProtoOAGetAccountListByAccessTokenReq": 2149, "ProtoOAGetAccountListByAccessTokenRes": 2150,
    "ProtoOAAccountLogoutReq": 2162, "ProtoOAAccountLogoutRes": 2163, "ProtoOAAccountDisconnectEvent": 2164,
    "ProtoOARefreshTokenReq": 2173, "ProtoOARefreshTokenRes": 2174,
    "ProtoOAGetPositionUnrealizedPnLReq": 2187, "ProtoOAGetPositionUnrealizedPnLRes": 2188,
}
NAME_OF = {v: k for k, v in PAYLOAD.items()}

#: the enum values this system reads or sends (official names and numbers)
TRADE_SIDE = {"BUY": 1, "SELL": 2}
ORDER_TYPE = {"MARKET": 1, "LIMIT": 2, "STOP": 3, "STOP_LOSS_TAKE_PROFIT": 4, "MARKET_RANGE": 5, "STOP_LIMIT": 6}
EXECUTION_TYPE = {2: "ORDER_ACCEPTED", 3: "ORDER_FILLED", 4: "ORDER_REPLACED", 5: "ORDER_CANCELLED",
                  6: "ORDER_EXPIRED", 7: "ORDER_REJECTED", 8: "ORDER_CANCEL_REJECTED", 9: "SWAP",
                  10: "DEPOSIT_WITHDRAW", 11: "ORDER_PARTIAL_FILL", 12: "BONUS_DEPOSIT_WITHDRAW"}
ACCOUNT_TYPE = {0: "HEDGED", 1: "NETTED", 2: "SPREAD_BETTING"}
ACCESS_RIGHTS = {0: "FULL_ACCESS", 1: "CLOSE_ONLY", 2: "NO_TRADING", 3: "NO_LOGIN"}
TRADING_MODE = {0: "ENABLED", 1: "DISABLED_WITHOUT_PENDINGS_EXECUTION", 2: "DISABLED_WITH_PENDINGS_EXECUTION",
                3: "CLOSE_ONLY_MODE"}
SWAP_CALCULATION = {0: "PIPS", 1: "PERCENTAGE", 2: "POINTS"}

_VARINT = ("int64", "uint64", "int32", "uint32", "bool", "enum")
_SCALAR = _VARINT + ("double", "string", "bytes")
_RANGE = {"int64": (-2 ** 63, 2 ** 63 - 1), "uint64": (0, 2 ** 64 - 1), "int32": (-2 ** 31, 2 ** 31 - 1),
          "uint32": (0, 2 ** 32 - 1), "enum": (-2 ** 31, 2 ** 31 - 1)}
_WIRE = {**{t: 0 for t in _VARINT}, "double": 1, "string": 2, "bytes": 2}


def _parse(spec: str) -> dict[str, dict[str, tuple[int, str, bool]]]:
    out: dict[str, dict[str, tuple[int, str, bool]]] = {}
    for line in spec.strip().splitlines():
        name, _, body = line.partition(":")
        fields: dict[str, tuple[int, str, bool]] = {}
        for part in filter(None, (p.strip() for p in body.split(";"))):
            lhs, typ = part.split()
            fname, num = lhs.split("=")
            rep = typ.endswith("*")
            fields[fname] = (int(num), typ.rstrip("*"), rep)
        out[name.strip()] = fields
    for name, fields in out.items():
        nums = [n for n, _, _ in fields.values()]
        assert len(nums) == len(set(nums)), f"{name}: a field number is used twice"
        for f, (_, typ, _) in fields.items():
            assert typ in _SCALAR or typ in out, f"{name}.{f}: unknown type {typ}"
    return out


SCHEMA = _parse(_SPEC)


def schema_hash() -> str:
    """The schema's fingerprint: the golden fixture records the one it was checked against."""
    return hashlib.sha256(_SPEC.strip().encode()).hexdigest()


# ── encoding ────────────────────────────────────────────────────────────────

def _varint(n: int) -> bytes:
    n &= 0xFFFFFFFFFFFFFFFF  # negative numbers: two's complement over 64 bits (ten bytes), as protobuf does
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _scalar(where: str, typ: str, v) -> bytes:
    if typ == "bool":
        if not isinstance(v, bool):
            raise ProtoError(f"{where}: a bool is required, got {v!r}")
        return _varint(int(v))
    if typ in _RANGE:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ProtoError(f"{where}: an integer is required, got {v!r}")
        lo, hi = _RANGE[typ]
        if not lo <= v <= hi:
            raise ProtoError(f"{where}: {v} is outside {typ}")
        return _varint(v)
    if typ == "double":
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ProtoError(f"{where}: a finite number is required, got {v!r}")  # a NaN price is never sent
        return struct.pack("<d", float(v))
    if typ == "string":
        if not isinstance(v, str):
            raise ProtoError(f"{where}: a string is required, got {type(v).__name__}")
        b = v.encode("utf-8")
        return _varint(len(b)) + b
    if typ == "bytes":
        if not isinstance(v, (bytes, bytearray)):
            raise ProtoError(f"{where}: bytes are required, got {type(v).__name__}")
        return _varint(len(v)) + bytes(v)
    raise ProtoError(f"{where}: unknown type {typ}")


def encode(name: str, fields: dict) -> bytes:
    """One message's bytes, fields in number order (as Google's runtime writes them). A field the schema does not know
    is refused: a typo must not silently drop a stop loss."""
    schema = SCHEMA.get(name)
    if schema is None:
        raise ProtoError(f"unknown message {name}")
    unknown = sorted(set(fields) - set(schema))
    if unknown:
        raise ProtoError(f"{name}: unknown fields {unknown}")
    out = bytearray()
    for fname, (num, typ, rep) in sorted(schema.items(), key=lambda kv: kv[1][0]):
        if fname not in fields or fields[fname] is None:
            continue
        values = fields[fname] if rep else [fields[fname]]
        if rep and not isinstance(values, (list, tuple)):
            raise ProtoError(f"{name}.{fname}: a list is required")
        for v in values:
            where = f"{name}.{fname}"
            if typ in SCHEMA:
                if not isinstance(v, dict):
                    raise ProtoError(f"{where}: a {typ} (dict) is required")
                body = encode(typ, v)
                out += _varint(num << 3 | 2) + _varint(len(body)) + body
            else:
                out += _varint(num << 3 | _WIRE[typ]) + _scalar(where, typ, v)
    return bytes(out)


# ── decoding ────────────────────────────────────────────────────────────────

def _read_varint(b: bytes, i: int) -> tuple[int, int]:
    n = shift = 0
    while True:
        if i >= len(b):
            raise ProtoError("truncated varint")
        c = b[i]
        i += 1
        n |= (c & 0x7F) << shift
        if not c & 0x80:
            return n & 0xFFFFFFFFFFFFFFFF, i
        shift += 7
        if shift >= 70:
            raise ProtoError("varint longer than ten bytes")


def _from_varint(typ: str, n: int):
    if typ == "bool":
        return n != 0
    if typ == "uint64":
        return n
    if typ == "int64":
        return n - (1 << 64) if n >= 1 << 63 else n
    if typ == "uint32":
        return n & 0xFFFFFFFF
    n &= 0xFFFFFFFF  # int32 and enum: the low 32 bits, signed
    return n - (1 << 32) if n >= 1 << 31 else n


def _skip(b: bytes, i: int, wt: int) -> int:
    if wt == 0:
        return _read_varint(b, i)[1]
    if wt == 1:
        j = i + 8
    elif wt == 2:
        ln, i = _read_varint(b, i)
        j = i + ln
    elif wt == 5:
        j = i + 4
    else:
        raise ProtoError(f"wire type {wt} is not supported")
    if j > len(b):
        raise ProtoError("truncated field")
    return j


def decode(name: str, data: bytes) -> dict:
    """The message's known fields; fields this schema does not describe are skipped. A field absent from the bytes is
    absent from the dict (never its default), and an explicit false or zero is kept: absence and 'no' differ."""
    schema = SCHEMA.get(name)
    if schema is None:
        raise ProtoError(f"unknown message {name}")
    by_num = {num: (fname, typ, rep) for fname, (num, typ, rep) in schema.items()}
    out: dict = {}
    b, i = bytes(data), 0
    while i < len(b):
        key, i = _read_varint(b, i)
        num, wt = key >> 3, key & 7
        if num == 0:
            raise ProtoError(f"{name}: field number 0")
        if num not in by_num:
            i = _skip(b, i, wt)
            continue
        fname, typ, rep = by_num[num]
        where = f"{name}.{fname}"
        if typ in SCHEMA or typ in ("string", "bytes"):
            if wt != 2:
                raise ProtoError(f"{where}: wire type {wt}, expected 2")
            ln, i = _read_varint(b, i)
            if i + ln > len(b):
                raise ProtoError(f"{where}: truncated")
            chunk, i = b[i:i + ln], i + ln
            if typ in SCHEMA:
                vals = [decode(typ, chunk)]
            elif typ == "string":
                try:
                    vals = [chunk.decode("utf-8")]
                except UnicodeDecodeError as e:
                    raise ProtoError(f"{where}: not UTF-8") from e
            else:
                vals = [chunk]
        elif wt == _WIRE[typ]:
            if typ == "double":
                if i + 8 > len(b):
                    raise ProtoError(f"{where}: truncated")
                vals, i = [struct.unpack("<d", b[i:i + 8])[0]], i + 8
            else:
                n, i = _read_varint(b, i)
                vals = [_from_varint(typ, n)]
        elif wt == 2 and rep:  # a packed repeated scalar: parsers accept it whatever the definition says
            ln, i = _read_varint(b, i)
            end = i + ln
            if end > len(b):
                raise ProtoError(f"{where}: truncated")
            vals = []
            while i < end:
                if typ == "double":
                    if i + 8 > end:
                        raise ProtoError(f"{where}: truncated")
                    vals.append(struct.unpack("<d", b[i:i + 8])[0])
                    i += 8
                else:
                    n, i = _read_varint(b, i)
                    vals.append(_from_varint(typ, n))
            if i != end:
                raise ProtoError(f"{where}: packed field overruns")
        else:
            raise ProtoError(f"{where}: wire type {wt}, expected {_WIRE[typ]}")
        if rep:
            out.setdefault(fname, []).extend(vals)
        else:
            out[fname] = vals[-1]  # the last one wins, as protobuf defines it
    return out


# ── the envelope and the frame ──────────────────────────────────────────────

def envelope(name: str, fields: dict, client_msg_id: str | None = None) -> bytes:
    """A ProtoMessage carrying one message. The inner message's own payloadType field is left out, as the official
    clients leave it."""
    if name not in PAYLOAD:
        raise ProtoError(f"{name} is not a top-level message")
    env = {"payloadType": PAYLOAD[name], "payload": encode(name, fields)}
    if client_msg_id is not None:
        env["clientMsgId"] = client_msg_id
    return encode("ProtoMessage", env)


def open_envelope(data: bytes) -> tuple[int, bytes, str | None]:
    env = decode("ProtoMessage", data)
    if "payloadType" not in env:
        raise ProtoError("a ProtoMessage without payloadType")
    return env["payloadType"], env.get("payload", b""), env.get("clientMsgId")


def frame(data: bytes) -> bytes:
    if len(data) > MAX_FRAME:
        raise ProtoError(f"a frame of {len(data)} bytes is over the limit")
    return struct.pack(">I", len(data)) + data
