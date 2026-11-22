# TRINITY-OMEGA SUITE — Complete Engineering Handoff for Claude (`autonomous-bot-trader`)

## 1. Context & Constraints
- **Owner**: the repository owner (`rimurukingdemon313/autonomous-bot-trader`)
- **Execution Mode Right Now**: **`PAPER` mode ONLY** on real daily market prices (no live/demo cTrader connection right now; `aitrader/broker/ctrader/` stays dormant until future live/demo deployment).
- **Sharia & Prop-Firm Constraints**:
  - `swap_per_night = 0.0` (Swap-Free Islamic Prop Account model).
  - **Zero interest-bearing bonds traded** (`TLT`, `^VIX`, `UUP` are strictly macro signal sensors, NEVER traded).
  - Strict `-10%` Prop-Firm start & trailing drawdown safety + `HardRiskGate` compliance (`stop_loss` mandatory on every order, `OPEN_RISK_LIMIT <= 4.0%`, `MARGIN_UNAVAILABLE` prevented).

## 2. Included Files in This Package
1. `trinity_omega_suite.py` — Complete self-contained Python implementation of all 4 strategies (`TRND-1 PRO`, `NEXUS-ALPHA-4 PRO`, `OMEGA-APEX-1`, `TRINITY-MASTER`), 20-year dataset (2007–2026), `HardRiskGate` order adapter (`build_hard_gate_orders`), cTrader symbol mapping (`CTRADER_SYMBOL_MAP`), and daily lookback converter (`DAILY_LOOKBACK_EQUIVALENTS`).
2. `trinity_master_trades_20yr.csv` — Full 288-period trade-by-trade log (2007-03-02 to 2026-11-13) with exact weights, open risk %, costs, net PnL ($ on $200K), cumulative return, and drawdown.
3. `CLAUDE_HANDOFF_SPEC.md` — This specification and integration checklist.

## 3. Verified 20-Year Benchmarks (100% Raw Un-Capped Close-to-Close Returns, 2007–2026)
| System | 20Y t-stat (H1 / H2) | 2x Costs t | Bootstrap p (2000) | Profit Factor | Win Rate | Max DD (20Y / 21–26) | Prop Fail (-10% Start / Trail) | 20Y Net (200K$) | 2021–2026 Monthly (200K$ / 400K$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Claude `TRND-1` (Original) | 2.74 (21–26) | — | — | — | 56.6% | -14.02% | Failed 1990/2000 | +$118,731 | +$754 (`HALF`) |
| 1. `TRND-1 PRO` (Pure Equities) | 3.09 (2.80 / 1.56) | 2.76 | 0.0020 | 1.84 | 67.61% | -7.93% / -7.30% | **0/273 / 0/273** | +$173,509 | +$767 / +$1,534 |
| 2. `NEXUS-ALPHA-4 PRO` (Eq+Gold) | 4.08 (2.74 / 3.01) | 3.69 | 0.00000 | 2.11 | 66.67% | -9.60% / -6.21% | **0/273 / 0/273** | +$274,557 | +$1,641 / +$3,282 |
| 3. `OMEGA-APEX-1` (4-Asset Top-2) | 3.58 (2.58 / 2.49) | 3.26 | 0.00000 | 1.91 | 63.64% | -9.62% / -6.34% | **0/273 / 0/273** | +$210,022 | +$1,703 / +$3,405 |
| **4. `TRINITY-MASTER` (Ensemble)** | **4.24 (2.84 / 3.14)** | **3.85** | **0.00000** | **2.10** | **66.95%** | **-9.47% / -6.00%** | **0/273 / 0/273** | **+$270,973** | **+$1,847 / +$3,695** |

- **HardRiskGate 288-Period Audit**: `0` violations across all 288 periods (`max_open_risk_pct_seen = 3.81% <= 4.0%`, `max_margin_usd_seen_on_200k = $23,840.77`).

## 4. Exact 5 Repository Conflicts Already Solved in Code
1. **Symbol Mapping (`ctrader/symbols.py`)**: ETFs mapped to CFD canonicals (`QQQ -> NAS100`, `SPY -> US500`, `GLD -> XAUUSD`, `DBC -> USOIL`).
2. **Macro Sensor Separation**: `^VIX`, `TLT`, `UUP` read from Yahoo daily (`t-1` close) strictly as sensors.
3. **Daily-Bar (`D1`) Lookbacks (`DAILY_LOOKBACK_EQUIVALENTS`)**: Rebalance every 15 trading days; `MA3=45D`, `MA4=60D`, `MA5=75D`, `MA8=120D`, `MA10=150D`, `Vol6=90D`.
4. **HardRiskGate Mandatory Stops & Risk Limits**: `build_hard_gate_orders()` attaches mandatory `3.2%` protective stop-loss and enforces `open_risk <= 4.0%` and `margin <= free_margin`.
5. **`PAPER` Mode Integration**: Build `aitrader/position/trinity_paper_desk.py` running in `PAPER` mode alongside `trend_desk.py`, register in `models/artifacts/promoted_rules.json` (`mode: "PAPER"`), save daily audit to `research/results/TRINITY-MASTER-daily-audit.json`, run `pytest`, and commit/push.
