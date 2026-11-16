# cTrader demo connection

**What exists:** a connection to cTrader's Open API, used for DEMO accounts only. It comes with a probe that checks
the account and measures its prices. **The probe places no order.**

**What does not exist yet:** the trend desk does not trade a broker account. Orders, stop moves and closes are the
next piece of work ("What comes next" below).

## Why cTrader

The owner's route to the target runs through funded (prop-firm) accounts trading TRND-1 (`docs/FUNDED_PAPER.md`).
That needs a broker connection a server can run by itself, and cTrader fits:

- **It runs from a server.** cTrader's Open API is reachable from GitHub's runners. MetaTrader 4 and 5 need their own
  terminal running on Windows.
- **Demo and live are separate proxies.** `demo.ctraderapi.com` serves demo accounts and `live.ctraderapi.com` serves
  live ones.
- **The broker reports the account's type itself.** The account list carries `isLive` and the account record carries
  `swapFree`.
- **Prop firms offer it.** Review sites list cTrader among FTMO's platforms, and Spotware announced a swap-free
  account type for cTrader brokers. **These are web search results only; nothing here was confirmed with a firm.**

## What is checked, and where

Every check fails when its evidence is absent (CLAUDE.md rules 1 and 7).

| Check | Our signal | The broker's signal | Code |
|---|---|---|---|
| DEMO | the connection goes to `demo.ctraderapi.com`, a module constant with no setting that can change it; any other host is refused before connecting | the account list for the token marks the configured account `isLive = false`. A missing field fails, `true` fails, and two accounts with the same login fail | `transport.py`, `guard.verify_demo` |
| The right account | — | the account record the broker returns after authorisation is the account that passed the demo check (`ctidTraderAccountId`, and `traderLogin` when present) | `session.open_session` |
| Swap-free (the owner's condition) | — | the account record says `swapFree = true`. A missing field or `false` means the account is not used for orders, and the probe says so | `guard.verify_swap_free` |

Order of operations:

1. The application is authenticated.
2. The token's account list is read and the demo check runs.
3. Only after the check passes is the account authorised and its record read.

A refused account is never authorised and is asked nothing more. A test checks this against a fake proxy over a real
socket. Failure messages name the fields they read (rule 1), and never an account number, because they reach public
logs.

## The wire format

Protobuf 2 messages travel in a `ProtoMessage` envelope, each frame prefixed by its length, over TLS to port 5035. The
hosts and port come from Spotware's own Python SDK (`spotware/OpenApiPy`, `EndPoints`).

The codec (`aitrader/broker/ctrader/proto.py`) describes only the 55 messages this system uses. It was checked against
cTrader's official definitions (`spotware/openapi-proto-messages`, commit `a9676f27`, 2026-11-04):

- every one of its 284 fields matched by name, number, type and repetition;
- all 42 payload types matched;
- every enum value used matched;
- its bytes equal those of Google's protobuf runtime (7.36.2) for every message.

That includes negative and ten-byte integers, numbers past int64, explicit `false`, non-ASCII text, and nested and
repeated messages. Official messages with every field set also decode to exactly the schema's fields.

`scripts/ctrader_golden.py` re-runs the check and rewrites `tests/fixtures/ctrader_golden.json`. A test fails if the
schema is edited without re-running it.

The decoder keeps absence visible: a field the broker left out is absent, never `false` or `0`. A NaN or infinite
price can never be encoded, and a misspelt field name is refused rather than silently dropped.

**Writes are never retried (CLAUDE.md rule 3).** This release sends no write. When orders are built, an unanswered
order will raise `AmbiguousExecution`, and the only recovery will be to read the account's positions and orders
(`ProtoOAReconcileReq`).

## The probe (`scripts/ctrader_probe.py`, `.github/workflows/ctrader-probe.yml`)

It is started by hand (Actions → "cTrader demo probe (no orders)" → Run workflow). It publishes `REPORT.md` and
`probe.json` to the `ctrader-data` branch, keeping every run under `probes/`.

The report has:

- **The checks:** demo and swap-free, each with its reason.
- **The account:** the broker, the account type, access rights, the token's scope (VIEW or TRADE), the deposit
  currency, balance and leverage.
- **The desk's four indices at this broker:** found by their usual names (`US500`/`US500.cash`/`SPX500`,
  `NAS100`/`US100.cash`/`USTEC`, `GER40`/`DE40`, `UK100`/`FTSE100`), with their volume steps, swap terms, trading
  hours and commission fields.
- **Spreads over a window of real prices:** median, 90th percentile and maximum in index points and in basis points,
  next to the spread the desk assumes (US500 0.5, NAS100 1.5, GER40 1.5, UK100 1.0).
  - A price update can carry one side only, so a spread is counted only when both sides are known.
  - A window with no prices (a closed market) is reported as no prices, never as a zero spread.

It never refreshes the token. A refresh token can be used once ("the refresh token has no expiry, but you can only use
it once", the official SDK's documentation), so refreshing it here would leave the stored secret dead.

## What the owner does (free; no money is spent)

1. **Open a cTrader demo account** at the firm or broker to be used (for example a firm's free trial on cTrader).
2. **Register an application** at `openapi.ctrader.com`, signed in with the same cTrader ID, and wait until it is
   active. It gives a Client ID and a Client Secret.
3. **Get an access token** for that cTrader ID from the application (Spotware's OAuth flow: the authorisation page,
   then the token endpoint `https://openapi.ctrader.com/apps/token`). Keep the refresh token too.
4. **Add five repository secrets** in GitHub (Settings → Secrets and variables → Actions → New repository secret).
   Never paste them in a chat, an issue or a file.
   - `CTRADER_CLIENT_ID`
   - `CTRADER_CLIENT_SECRET`
   - `CTRADER_ACCESS_TOKEN`
   - `CTRADER_ACCOUNT_LOGIN`: the account's number as cTrader shows it
   - `CTRADER_REFRESH_TOKEN`: stored for the next piece; the probe never uses it
5. **Run the probe.** If a secret is missing, the run fails and names the missing secrets. If the demo check fails,
   it says which field failed.

Steps 2 and 3 follow Spotware's SDK documentation. Spotware's help site could not be reached from the director's
session, so the exact screens were not seen.

## What comes next (not built)

- **`CTraderBroker`:** the system's `Broker` protocol over this connection.
  - A market order with its stop, waiting for the fill.
  - An unanswered write raises `AmbiguousExecution` and is resolved only by reading the account.
  - Stop moves (`ProtoOAAmendPositionSLTPReq`) and closes.
  - The demo check repeated before order creation and before submission.
  - Orders refused on an account that is not swap-free.
- **The desk acting on a real clock:** the month-end decision minutes before each exchange's close, the 6% stop moved
  each evening, and the minimal trades for a phase's first four days. This is the schedule decided on 2026-11-07
  (`docs/FUNDED_PAPER.md`), through the same risk engine and hard gate as the paper desk.
- **Keeping the token alive:** each refresh returns a new refresh token, and it has to be stored somewhere private.
- **Money:** challenges are bought only on the owner's explicit word. Nothing here spends money.
