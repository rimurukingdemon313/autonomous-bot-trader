# cTrader demo connection

**What exists:**

- **A connection to cTrader's Open API, for DEMO accounts only.**
- **A probe** that checks the account and measures its prices. The probe places no order.
- **The system's broker interface on that connection** (`CTraderBroker`): orders, stop moves and closes. They go
  through the hard risk gate's permits, exactly as on the paper broker.

**What does not exist yet:** nothing runs the trend desk against a broker account. The runner that will do it is the
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

## The broker (`aitrader/broker/ctrader/broker.py`)

`CTraderBroker` implements the system's `Broker` protocol, so the execution engine, the hard risk gate and the risk
engine drive it exactly as they drive the paper broker. There is one write path and one source of size (CLAUDE.md
rules 2 and 14).

| | |
|---|---|
| **Each write needs the gate's permit** | An order, a stop move or a close is accepted only with the gate's single-use permit for exactly that write. A broker with no gate attached sends nothing. |
| **Writes are sent once (rule 3)** | `Client.write` sends the message once and waits for its terminal execution event. An error answer carrying the write's id is a rejection. If no answer comes in time, the connection is lost, or the send fails after it began, the result is `AmbiguousExecution`. It is never sent again from anywhere. The execution engine then reads the account by client id (`label` and `clientOrderId` carry it). |
| **Demo at every write (rule 1)** | Before a write is created, the demo check runs again from the broker's account list, and swap-free is read again from the account record. Just before sending, the host and that verdict are checked once more. A failed check refuses the write and calls `on_refusal`, which the runner will wire to the kill switch. |
| **Orders** | A market order carries its stop as `relativeStopLoss`: cTrader takes no absolute stop on a market order. With slippage the stop is that far from the actual fill, and the next evening's stop move sets it exactly. The volume must be whole steps at or above the minimum, and the stop must be on the loss side of the live price. Otherwise nothing is sent. |
| **Stop moves** | `ProtoOAAmendPositionSLTPReq`. The result is confirmed by reading the position. If no answer came but the broker holds the new stop, it is accepted. If the broker holds anything else, the move is ambiguous. |
| **Closes** | The P/L is the change in the broker's own balance across the closing deal. |
| **Stops hit while away** | Read from the closing deals with their P/L **unknown** (None). The deal reports commission and swap without a documented sign convention, and the balance before it is not in the deal. The gross profit is kept. |
| **Equity** | The broker's balance plus its own net unrealized P/L. A balance without its `moneyDigits` is an error, never a number. |
| **Conversion** | Another currency is converted at the broker's own listed pair (EURUSD for GER40 on a USD account). With no such pair there is no spec, so nothing is sized. |

Tests: `tests/unit/test_ctrader_broker.py`, against a fake proxy that trades and through the real gate. It can be set
to stay silent, to apply a write but lose the answer, or to refuse. Each `ctrader-broker-` mutant is killed.

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

- **A first round trip on the demo account:** the minimum volume of one index, opened with its stop, moved and
  closed. It confirms the execution events and the P/L sign convention on the real server before the desk uses it.
- **The desk acting on a real clock:** the month-end decision minutes before each exchange's close, the 6% stop moved
  each evening, and the minimal trades for a phase's first four days. This is the schedule decided on 2026-11-07
  (`docs/FUNDED_PAPER.md`), through the same risk engine and hard gate as the paper desk.
- **Keeping the token alive:** each refresh returns a new refresh token, and it has to be stored somewhere private.
- **Money:** challenges are bought only on the owner's explicit word. Nothing here spends money.
