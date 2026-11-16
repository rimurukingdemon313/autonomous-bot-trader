"""Two checks before an account is used, each from the broker's own record and each failing on absence.

DEMO (CLAUDE.md rule 1): ours, the connection goes to the demo proxy (a constant, transport.DEMO_HOST); the broker's,
the account list it returns for the token marks this account isLive = false. A missing isLive fails; a true fails.

SWAP-FREE (the owner's condition: no interest paid or received): the broker's account record (ProtoOATrader) says
swapFree = true. A missing field fails: an account is never assumed swap-free.

The messages name the fields read, never an account number: they reach public logs.
"""

from __future__ import annotations

from dataclasses import dataclass

from .transport import DEMO_HOST, LIVE_HOST


@dataclass(frozen=True)
class Verdict:
    ok: bool
    why: str
    looked_at: tuple[str, ...]
    account_id: int | None = None


def verify_demo(host: str, accounts: list[dict], login: int) -> Verdict:
    looked = ("connection host", "ctidTraderAccount[].traderLogin", "ctidTraderAccount[].isLive")
    if host == LIVE_HOST or host != DEMO_HOST:
        return Verdict(False, f"our signal fails: the connection host is {host!r}, not {DEMO_HOST}", looked)
    if isinstance(login, bool) or not isinstance(login, int):
        return Verdict(False, "the configured account login is not a number", looked)
    mine = [a for a in accounts if a.get("traderLogin") == login]
    if not mine:
        return Verdict(False, f"the token lists {len(accounts)} account(s) and none has the configured login "
                              "(CTRADER_ACCOUNT_LOGIN)", looked)
    if len(mine) > 1:
        return Verdict(False, f"{len(mine)} accounts listed for the token have the configured login: which one is "
                              "meant cannot be told, so none is used", looked)
    a = mine[0]
    if "isLive" not in a:
        return Verdict(False, "the broker's account record has no isLive field: absence of evidence fails", looked)
    if a["isLive"] is not False:
        return Verdict(False, "the broker marks this account LIVE (isLive = true): refused", looked)
    if not isinstance(a.get("ctidTraderAccountId"), int):
        return Verdict(False, "the broker's account record has no ctidTraderAccountId", looked)
    return Verdict(True, f"demo: the host is {DEMO_HOST} and the broker marks the account isLive = false", looked,
                   a["ctidTraderAccountId"])


def verify_swap_free(trader: dict) -> Verdict:
    looked = ("ProtoOATrader.swapFree",)
    if "swapFree" not in trader:
        return Verdict(False, "the broker's account record has no swapFree field: the account is not shown to be "
                              "swap-free, so it is not used for orders", looked)
    if trader["swapFree"] is not True:
        return Verdict(False, "the broker reports this account is NOT swap-free (swapFree = false): it would pay or "
                              "receive swap, so it is not used for orders", looked)
    return Verdict(True, "swap-free: the broker's account record says swapFree = true", looked)
