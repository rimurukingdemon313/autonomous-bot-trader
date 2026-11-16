"""Opening a session on the demo account (docs/CTRADER.md): the application, the accounts the token grants, the demo
check, the account itself, and the swap-free check, in that order. Nothing is asked of an account before it has
passed the demo check.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .client import Client
from .guard import Verdict, verify_demo, verify_swap_free
from .transport import DemoRefused

ENV = ("CTRADER_CLIENT_ID", "CTRADER_CLIENT_SECRET", "CTRADER_ACCESS_TOKEN", "CTRADER_ACCOUNT_LOGIN")
SCOPES = {0: "SCOPE_VIEW", 1: "SCOPE_TRADE"}


@dataclass(frozen=True, repr=False)
class Credentials:
    """From the host's secret settings only (GitHub secrets, Railway variables): never a file, a log or a report."""

    client_id: str
    client_secret: str
    access_token: str
    login: int

    def __repr__(self) -> str:
        return "Credentials(<hidden>)"

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> tuple[Credentials | None, list[str]]:
        """The credentials, or None and the names of the settings that are missing or malformed."""
        missing = [k for k in ENV if not (env.get(k) or "").strip()]
        if missing:
            return None, missing
        login = env["CTRADER_ACCOUNT_LOGIN"].strip()
        if not login.isdigit():
            return None, ["CTRADER_ACCOUNT_LOGIN (must be the account's number)"]
        return cls(env["CTRADER_CLIENT_ID"].strip(), env["CTRADER_CLIENT_SECRET"].strip(),
                   env["CTRADER_ACCESS_TOKEN"].strip(), int(login)), []

    def secrets(self) -> tuple[str, ...]:
        return (self.client_id, self.client_secret, self.access_token, str(self.login))


def scrub(text: str, secrets: tuple[str, ...]) -> str:
    """Any secret value that found its way into a message is replaced before the message is written anywhere."""
    for s in sorted((s for s in secrets if s and len(s) >= 4), key=len, reverse=True):
        text = text.replace(s, "[hidden]")
    return text


@dataclass
class Session:
    client: Client
    account_id: int
    trader: dict
    demo: Verdict
    swap_free: Verdict
    scope: str | None


def open_session(client: Client, creds: Credentials) -> Session:
    """Authenticate the application, verify the account is demo by the broker's own list, then authorise it and read
    its record. A failed demo check raises DemoRefused before the account is authorised."""
    client.call("ProtoOAApplicationAuthReq", {"clientId": creds.client_id, "clientSecret": creds.client_secret},
                ("ProtoOAApplicationAuthRes",))
    _, listed = client.call("ProtoOAGetAccountListByAccessTokenReq", {"accessToken": creds.access_token},
                            ("ProtoOAGetAccountListByAccessTokenRes",))
    demo = verify_demo(client.transport.host, listed.get("ctidTraderAccount", []), creds.login)
    if not demo.ok:
        raise DemoRefused(f"{demo.why}. Fields read: {', '.join(demo.looked_at)}")
    client.call("ProtoOAAccountAuthReq", {"ctidTraderAccountId": demo.account_id, "accessToken": creds.access_token},
                ("ProtoOAAccountAuthRes",))
    _, res = client.call("ProtoOATraderReq", {"ctidTraderAccountId": demo.account_id}, ("ProtoOATraderRes",))
    trader = res.get("trader") or {}
    if trader.get("ctidTraderAccountId") != demo.account_id or (
            "traderLogin" in trader and trader["traderLogin"] != creds.login):
        raise DemoRefused("the account record the broker returned is not the account that passed the demo check. "
                          "Fields read: ProtoOATrader.ctidTraderAccountId, ProtoOATrader.traderLogin")
    return Session(client, demo.account_id, trader, demo, verify_swap_free(trader),
                   SCOPES.get(listed.get("permissionScope")))
