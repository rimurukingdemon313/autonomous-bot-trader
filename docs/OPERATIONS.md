# Operations: running on Railway (paper or demo)

## What runs

One process (`python -m aitrader`):

- HTTP API + dashboard on `$PORT`:
  - `/` the dashboard;
  - `/healthz` liveness (the process and its database answer; Railway's health check);
  - `/readyz` readiness: 200 only when decisions can be made safely (database, verified knowledge base,
    startup reconciliation clean, kill switch readable, broker account readable). Paused is still
    ready; the body lists every reason it is not;
  - `/metrics` Prometheus text (counts, forward net/cost R, provider calls/tokens/cost, `live_trading 0`);
  - `/api/*` read models, including `/api/evidence` (forward evidence) and `/api/lessons`;
- the scheduler: 90 s after every H1 close it resolves outcomes, closures
  and time exits; every **4th** H1 close (UTC hours 0, 4, 8, …) it also
  decides. 4 is the cadence the knowledge base was built and tested with,
  read from its card: deciding more often would run a system whose trade
  frequency was never measured;
- the position monitor: every 20 s, newly closed bars are applied to the
  paper account's stops/targets and to the outcome tracker; every 5 min the
  forward ledger resolves proposals whose outcome completed bars now reveal
  (docs/FORWARD_VALIDATION.md).

State lives in **one SQLite file under `DATA_DIR`** plus the live pattern
memory (`memory_live.npz`). Mount a Railway **Volume** at `/data` so a
restart or redeploy keeps every trade, decision, lesson and reflection.
Without one, every redeploy starts from an empty disk: the paper account is
back at its start balance and the bot is paused again. The dashboard's
**STORAGE** chip says which it is (Railway sets `RAILWAY_VOLUME_MOUNT_PATH`
only when a volume is attached): `SAVED ON VOLUME`, or `NOT PERSISTENT` in red.

## Deploy

1. Railway -> New Project -> Deploy from GitHub repo
   `rimurukingdemon313/autonomous-bot-trader`. The `Dockerfile` and
   `railway.json` are picked up automatically (health check `/healthz`,
   restart on failure).
2. Add a **Volume**, mount path `/data`. Railway mounts it owned by root;
   the image's entrypoint hands it to the service user (uid 10001) and drops
   root before the service starts. No extra setting is needed.
3. Variables (Railway -> Variables; never in the repository) — see
   `.env.example` for the full list. Minimum for paper trading on live data:
   `MODE=PAPER`, `DATA_DIR=/data`, `DASHBOARD_TOKEN` (a long random string),
   and the four `TRADELOCKER_*` credentials of a **demo** account.
4. Open the service URL: the dashboard. **It starts paused** (the knowledge
   base FAILED its pre-registered test, docs/SYSTEM_LIFECYCLE.md Amendment 2).
   Trading starts only when you press Resume with the dashboard token.
   Before resuming, the status bar must show `DATA: CONNECTED`,
   `DATABASE: HEALTHY` and `KNOWLEDGE: LOADED · FAILED` (loaded and
   verified; FAILED is the knowledge base's research verdict).

Without TradeLocker credentials the service still starts and reports
`DATA: NOT CONNECTED`; it makes no decisions on invented prices.

If startup fails (for example the volume is not writable), the service
does not trade. It answers every request with HTTP 503 and the reason
(`{"system": "STARTUP_FAILED", "reason": ...}`), and the deploy's health
check fails, so the reason is on the URL and in the logs.

## Where prices come from

- **`DATA_SOURCE=yahoo` (PAPER only).** Prices come from Yahoo Finance's
  public chart data, with no broker, account or key. The TradeLocker
  variables are ignored and can be deleted.
  - **Spread.** Yahoo publishes one price per bar, so the paper account
    pays a fixed, typical spread per pair. It is an estimate (EURUSD 0.8
    pip, GBPUSD 1.2, USDJPY 1.0, ...) and can be overridden with
    `PAPER_SPREAD_PIPS_<PAIR>`.
  - **Price time.** A price carries Yahoo's own timestamp, so a delay stays
    visible. With this source the risk engine accepts prices up to 90 s
    old (`RISK_MAX_QUOTE_AGE_S`).
  - **No FX volume.** Yahoo publishes none, so the one volume-based
    feature is excluded (and recorded as not provided), not reported as
    missing data.
  - **Rate of requests.** Prices are cached 10 s and bars per timeframe
    window.
  - **If Yahoo refuses.** The dashboard's DATA chip turns red with Yahoo's
    reason.
- **`DATA_SOURCE=tradelocker` (or `auto` with credentials).** The broker's
  own prices, needed for DEMO.

## Who decides

`DECISION_MODE=evidence` (default) is the quantitative system.
`DECISION_MODE=llm_trader` lets a language model propose trades, and it
also needs the `AI_*` variables (docs/AI_MODELS.md).
`DECISION_MODE=trading_room` makes one model per provider discuss in turn
as one team and write a joint decision (`AI_ROOM_*`, same document).
`DECISION_MODE=experimental_ai` has the first provider propose and specialists
on another provider challenge; a fixed rule decides (`AI_SPECIALISTS`, same document).
In either model mode, `DECISION_INTERVAL_MIN` (every N minutes) and
`SYMBOLS_PER_CYCLE` (pairs per cycle, in rotation) set how often it decides;
see docs/AI_MODELS.md for what each setting costs in model calls. An unknown value stops
the service at startup with a visible 503; it is never silently replaced.

## Modes

| MODE | Market data | Orders | Account |
|---|---|---|---|
| `PAPER` | TradeLocker (live) | simulated in-process | virtual, `PAPER_START_BALANCE` (default $20,000) |
| `DEMO` | TradeLocker (live) | TradeLocker **demo** account, after the two-signal demo check | the broker's demo balance |
| `LIVE` | — | **refused at startup** (`MODE=LIVE`, `LIVE_TRADING=true`, or any unknown value) | — |

Both PAPER and DEMO are **forward tests** of an unvalidated system while
PR-001 has not passed (docs/SYSTEM_LIFECYCLE.md, "Forward testing"). They
generate the only evidence no one could have seen in advance.

### Where an approved trade goes (edge status)

Every decision carries an **edge status** (docs/FORWARD_VALIDATION.md):
VALIDATED, PROMISING, EXPERIMENTAL or NONE. Today no edge is validated, so
every trade is **EXPERIMENTAL**.

| | PAPER | DEMO, `EXPERIMENTAL_EXECUTE=false` (default) | DEMO, `EXPERIMENTAL_EXECUTE=true` |
|---|---|---|---|
| VALIDATED | executed (simulated) | sent to the demo account | sent to the demo account |
| PROMISING / EXPERIMENTAL | executed (simulated) | **SHADOW**: risk-checked, recorded, followed forward, never sent | sent to the demo account |

The execution engine checks the same rule again before any order, so no
other code path can send an unvalidated trade. Shadow and executed trades
are measured identically in the forward ledger, after costs.

### Commands

Paper (the default; nothing reaches a broker):

    MODE=PAPER  LIVE_TRADING=false  DATA_DIR=/data  DASHBOARD_TOKEN=<long random>
    DATA_SOURCE=yahoo            # or TradeLocker demo credentials for broker prices
    DECISION_MODE=experimental_ai   AI_PROVIDERS=groq,gemini  AI_GROQ_API_KEY=...  AI_GROQ_MODEL=...
    AI_GEMINI_API_KEY=...  AI_GEMINI_MODEL=...

Demo, shadow only (orders are never sent for unvalidated trades):

    MODE=DEMO  PAPER_MODE=false  LIVE_TRADING=false  TRADELOCKER_EMAIL/PASSWORD/SERVER/ACCOUNT_ID=<demo account>

Demo, executing experimental trades on the **demo** account (explicit opt-in):

    MODE=DEMO  PAPER_MODE=false  LIVE_TRADING=false  EXPERIMENTAL_EXECUTE=true

Then open the dashboard and press **Resume** with the token. Locally:
`python -m aitrader` with the same variables in the environment.

## Controls

| Action | Token? | Effect |
|---|---|---|
| Emergency stop | no | kill switch on: no new orders until cleared |
| Pause | no | no new decisions become orders |
| Resume / Clear stop / Scan now / Revert knowledge | **yes** (`DASHBOARD_TOKEN`) | refused without it; refused entirely if no token is configured |

Open positions keep their broker-side stop and target when paused or stopped.

The token field survives a page reload in the same tab. Tick **Remember on
this device** to keep it in that browser across tabs and restarts; untick it
to forget it. A token the server refuses (401) is cleared, never kept. It is
stored only in your own browser, never sent anywhere but this dashboard, and
Emergency stop and Pause never need it.

## Restart and recovery

On startup, before any decision: open the database, restore experience and
lessons from the immutable episodes, load the knowledge base, and reconcile
with the broker:

- order intents left SUBMITTING/UNKNOWN are resolved by querying the broker
  by client id, never by resending;
- broker positions the journal does not know are **orphans**;
- journal positions the broker no longer holds are listed and closed from
  the broker's history at the next cycle (never with an invented exit);
- the account balance and equity are read.

If reconciliation fails, the account cannot be read, or orphans exist,
trading starts **paused** and the dashboard (and `/readyz`) says why.
Forward proposals not yet resolved are resolved after the restart from the
feed's completed bars: nothing about them lives only in memory.

## Logs

One JSON object per line on stdout (Railway -> Deployments -> Logs).
Secrets are redacted at the sink: values of `TRADELOCKER_PASSWORD`,
`TRADELOCKER_EMAIL`, `AI_API_KEY`, `DASHBOARD_TOKEN`, bearer tokens and JWTs.

## Rebuilding the knowledge base (research machine, not Railway)

    pip install -r requirements-research.txt
    python scripts/ingest_dukascopy.py          # ~1 hour, writes data/processed + data/manifest.json
    python scripts/build_knowledge.py           # writes models/artifacts/*
    python scripts/run_pr001.py                 # the pre-registered experiment
