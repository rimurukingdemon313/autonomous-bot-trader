# paper-forward-data — PAPER FORWARD TEST · NOT REAL MONEY

Written by `.github/workflows/paper-forward.yml` on `main`: the real service, `MODE=PAPER_FORWARD`, on a
$200,000 paper account, in 6-hour shifts.

| File | What |
|---|---|
| `REPORT.md` | the dashboard: account, P&L, risk status, the last decisions (decision → risk → paper execution), positions, trades |
| `paper_forward.json` | the same view in full (`/api/paper_forward`) |
| `aitrader.db.gz` | a snapshot of the paper account's database at the end of each shift |

The historical research status is unchanged: NO EDGE — DO NOT TRADE. Rules: `docs/PAPER_FORWARD.md` on `main`.
