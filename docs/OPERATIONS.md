# Operations: running on Railway (paper or demo)

## What runs

One process (`python -m aitrader`):

- HTTP API + dashboard on `$PORT` (`/` dashboard, `/healthz` health, `/api/*`);
- the scheduler: 90 s after every H1 close it resolves outcomes, closures
  and time exits; every **4th** H1 close (UTC hours 0, 4, 8, …) it also
  decides. 4 is the cadence the knowledge base was built and tested with,
  read from its card: deciding more often would run a system whose trade
  frequency was never measured;
- the position monitor: every 20 s, newly closed bars are applied to the
  paper account's stops/targets and to the outcome tracker.

State lives in **one SQLite file under `DATA_DIR`** plus the live pattern
memory (`memory_live.npz`). Mount a Railway **Volume** at `/data` so a
restart or redeploy keeps every trade, decision, lesson and reflection.

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

## Who decides

`DECISION_MODE=evidence` (default) is the quantitative system.
`DECISION_MODE=llm_trader` lets a language model propose trades, and it
also needs the `AI_*` variables (docs/AI_MODELS.md). An unknown value stops
the service at startup with a visible 503; it is never silently replaced.

## Modes

| MODE | Market data | Orders | Account |
|---|---|---|---|
| `PAPER` | TradeLocker (live) | simulated in-process | virtual, `PAPER_START_BALANCE` (default $20,000) |
| `DEMO` | TradeLocker (live) | TradeLocker **demo** account, after the two-signal demo check | the broker's demo balance |
| `LIVE` | — | **refused at startup** | — |

Both PAPER and DEMO are **forward tests** of an unvalidated system while
PR-001 has not passed (docs/SYSTEM_LIFECYCLE.md, "Forward testing"). They
generate the only evidence no one could have seen in advance.

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
with the broker (intents with unknown outcomes are resolved by querying the
broker, never by resending). If reconciliation fails or finds positions the
system did not open, trading starts **paused** and the dashboard says why.

## Logs

One JSON object per line on stdout (Railway -> Deployments -> Logs).
Secrets are redacted at the sink: values of `TRADELOCKER_PASSWORD`,
`TRADELOCKER_EMAIL`, `AI_API_KEY`, `DASHBOARD_TOKEN`, bearer tokens and JWTs.

## Rebuilding the knowledge base (research machine, not Railway)

    pip install -r requirements-research.txt
    python scripts/ingest_dukascopy.py          # ~1 hour, writes data/processed + data/manifest.json
    python scripts/build_knowledge.py           # writes models/artifacts/*
    python scripts/run_pr001.py                 # the pre-registered experiment
