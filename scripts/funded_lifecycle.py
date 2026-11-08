"""Descriptive only: what TRND-1's rule would have paid a trader on funded accounts, from every start month, with the
whole life of an account: the challenge fee, the two phases, monthly payouts at the profit split, the account lost at
the limits, and a new challenge bought after each loss. It uses FUNDED-P's own pieces (the rule's decisions, its
costs, HALF's one-day stop) on the four index CFDs, 1990-2026: data RC-EQ (1990-2020) and TRND-1-H (2021-2026)
already judged. It is not a test, and the past is not a forecast.

Assumptions, declared:
- a $200,000 challenge costs $1,100, refunded with the account's first payout, as FTMO does;
- phase 1 passes at +$20,000, phase 2 at +$10,000, each no earlier than its 4th trading day; then FUNDED;
- a day losing $10,000, or equity at $180,000, loses the account; a new challenge starts the next trading day;
- FUNDED: at each month's last trading day, any profit above $200,000 is paid out at an 80% split and the account
  goes back to $200,000;
- several accounts trade the same rule at the same size, so they win, lose and fail together: a plan of N accounts is
  N times one account, fees included.

    python scripts/funded_lifecycle.py <the TRND-1 data folder>   # -> research/results/FUNDED-lifecycle.json
"""

from __future__ import annotations

import json
import statistics
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.funded_paper as P  # noqa: E402
import scripts.trnd1 as T  # noqa: E402
from scripts.trnd1_funded_monthly import daily_pl  # noqa: E402

OUT = ROOT / "research" / "results" / "FUNDED-lifecycle.json"
FEE = 1_100.0
SPLIT = 0.80
HORIZONS = {"1 year": 252, "2 years": 504, "3 years": 756}
PLANS = {"3 accounts at FULL": ("FULL", 3), "6 accounts at HALF, with its stop": ("HALF", 6),
         "1 account at FULL": ("FULL", 1), "1 account at HALF, with its stop": ("HALF", 1)}


def lifecycle(days: list[tuple[date, float]], i0: int, n_days: int) -> dict:
    """One account's life from day i0 for n_days trading days: what it paid out, what it cost, what happened."""
    phase, equity, phase_days = 1, 0.0, 0
    fees, payouts, lost, refund_due = FEE, 0.0, 0, True
    first_payout, funded_days = None, 0
    window = days[i0:i0 + n_days]
    for k, (d, pl) in enumerate(window):
        equity += pl
        phase_days += 1
        if pl <= -P.DAILY_LOSS or equity <= -P.MAX_LOSS:  # the account is lost; a new challenge is bought
            lost += 1
            fees += FEE
            phase, equity, phase_days, refund_due = 1, 0.0, 0, True
            continue
        if phase in P.TARGETS and phase_days >= P.MIN_TRADING_DAYS and equity >= P.TARGETS[phase]:
            phase, equity, phase_days = phase + 1, 0.0, 0
            continue
        if phase == 3:
            funded_days += 1
            month_end = k + 1 == len(window) or window[k + 1][0].month != d.month
            if month_end and equity > 0:
                payouts += SPLIT * equity + (FEE if refund_due else 0.0)
                refund_due = False
                equity = 0.0
                if first_payout is None:
                    first_payout = k
    return {"net": payouts - fees, "payouts": payouts, "fees": fees, "lost": lost,
            "first_payout_day": first_payout, "funded_share": funded_days / len(window)}


def plan_summary(days: list[tuple[date, float]], accounts: int, n_days: int) -> dict:
    starts = [i for i, (d, _) in enumerate(days) if (i == 0 or days[i - 1][0].month != d.month)
              and i + n_days <= len(days)]
    lives = [lifecycle(days, i, n_days) for i in starts]
    net = sorted(accounts * x["net"] for x in lives)
    months = n_days / 21.0
    q = lambda p: net[min(len(net) - 1, int(p * len(net)))]  # noqa: E731
    first = sorted(x["first_payout_day"] for x in lives if x["first_payout_day"] is not None)
    return {"starts": len(lives), "mean_net": round(statistics.mean(net)), "median_net": round(statistics.median(net)),
            "p10_net": round(q(0.10)), "p90_net": round(q(0.90)), "worst_net": round(net[0]), "best_net": round(net[-1]),
            "share_losing_money": round(sum(n < 0 for n in net) / len(net), 3),
            "mean_net_a_month": round(statistics.mean(net) / months),
            "median_net_a_month": round(statistics.median(net) / months),
            "mean_accounts_lost": round(statistics.mean(x["lost"] for x in lives), 2),
            "never_paid": round(sum(x["first_payout_day"] is None for x in lives) / len(lives), 3),
            "median_months_to_first_payout": round(first[len(first) // 2] / 21.0, 1) if first else None,
            "mean_fees": round(accounts * statistics.mean(x["fees"] for x in lives))}


def first_months(days: list[tuple[date, float]], since: date, n_days: int) -> dict:
    """Where one account stands after its first n_days trading days, from every start month on or after `since`:
    still in phase 1, phase 1 passed, FUNDED reached, any payout, or lost."""
    starts = [i for i, (d, _) in enumerate(days) if d >= since and (i == 0 or days[i - 1][0].month != d.month)
              and i + n_days <= len(days)]
    tally = {"phase1_passed": 0, "funded": 0, "paid": 0, "lost": 0, "still_in_phase1": 0}
    for i0 in starts:
        phase, equity, phase_days, paid = 1, 0.0, 0, False
        for k, (d, pl) in enumerate(days[i0:i0 + n_days]):
            equity += pl
            phase_days += 1
            if pl <= -P.DAILY_LOSS or equity <= -P.MAX_LOSS:
                tally["lost"] += 1
                phase = 0
                break
            if phase in P.TARGETS and phase_days >= P.MIN_TRADING_DAYS and equity >= P.TARGETS[phase]:
                tally["phase1_passed" if phase == 1 else "funded"] += 1
                phase, equity, phase_days = phase + 1, 0.0, 0
                continue
            if phase == 3 and k + 1 < n_days and days[i0 + k + 1][0].month != d.month and equity > 0:
                paid, equity = True, 0.0
        tally["paid"] += paid
        tally["still_in_phase1"] += phase == 1
    n = len(starts)
    return {"starts": n, **{k: round(v / n, 3) for k, v in tally.items()}}


def main() -> int:
    T.DATA = Path(sys.argv[1])
    data = T.load(T.HOLDOUT_INDICES, date(1984, 1, 1), date(2026, 11, 1))
    series = {name: daily_pl(data, tr["expo"], tr["stop"])[0] for name, tr in P.TRACKS.items()}
    report = {"note": "descriptive, on data already judged (RC-EQ 1990-2020, TRND-1-H 2021-2026); not a test",
              "assumptions": {"fee": FEE, "split": SPLIT, "fee_refunded_with_first_payout": True,
                              "payout": "monthly, all profit above $200,000"}, "plans": {}}
    for plan, (track, n) in PLANS.items():
        report["plans"][plan] = {h: plan_summary(series[track], n, d) for h, d in HORIZONS.items()}
        for h, r in report["plans"][plan].items():
            print(plan, h, json.dumps(r))
    report["first_months_at_FULL"] = {
        f"{label}, {m} months": first_months(series["FULL"], since, 21 * m)
        for label, since in (("1990-2026", date(1990, 1, 1)), ("2021-2026", date(2021, 1, 1))) for m in (4, 5)}
    for k, v in report["first_months_at_FULL"].items():
        print("first months:", k, json.dumps(v))
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
