import math
from typing import Dict, List

SECTORS: Dict[str, str] = {
    "QQQ": "EQUITY", "SPY": "EQUITY", "IWM": "EQUITY",
    "GLD": "METALS", "SLV": "METALS",
    "USO": "ENERGY", "IBIT": "CRYPTO",
}

TAIL_CAPS: Dict[str, float] = {
    "QQQ": 0.55, "SPY": 0.65, "IWM": 0.55,
    "GLD": 0.30, "SLV": 0.12,
    "USO": 0.34, "IBIT": 0.25,
}


def _mom(ds: Dict[str, List[float]], a: str, t: int, w: int) -> float:
    w = max(1, min(w, t))
    return ds[a][t] / ds[a][t - w] - 1.0


def _rvol(rets: Dict[str, List[float]], a: str, t: int, w: int, dpb: float = 1.0) -> float:
    w = max(2, min(w, t))
    xs = rets[a][t - w + 1 : t + 1]
    m = sum(xs) / len(xs)
    v = math.sqrt(sum((x - m) ** 2 for x in xs) / max(len(xs) - 1, 1))
    return max(v / math.sqrt(dpb), 0.004)


def _allow_short(ds: Dict[str, List[float]], a: str, t: int, dpb: float, mode: str) -> bool:
    if mode == "none":
        return True
    if mode == "guard90":
        return _mom(ds, a, t, min(t, max(3, round(90 / dpb)))) < 0.0
    if mode == "bear05":
        return _mom(ds, a, t, min(t, max(3, round(90 / dpb)))) < -0.05
    return True


def apply_prop_shield(
    weights: Dict[str, float],
    current_drawdown: float,
    intraday_pnl_pct: float = 0.0,
) -> Dict[str, float]:
    """
    Applies the verified 2-step drawdown throttle plus live intraday prop-firm kill-switch.
    - Intraday kill-switch: flatten to 0.0 if intraday_pnl_pct <= -0.04 or current_drawdown <= -0.085
    - Drawdown throttle: <= -7.5% -> 0.25x | <= -5.0% -> 0.50x | else 1.00x
    """
    if intraday_pnl_pct <= -0.04 or current_drawdown <= -0.085:
        return {a: 0.0 for a in weights}
    scale = 0.25 if current_drawdown <= -0.075 else (0.50 if current_drawdown <= -0.05 else 1.0)
    return {a: round(w * scale, 4) for a, w in weights.items()}


def make_sec_tsmom_4(target_vol: float = 0.014, cap_mult: float = 0.95):
    """Strategy #3: SEC-TSMOM-4 (1.0x) — Pure Defensive Sector-Best Dual-Horizon TSMOM."""
    def engine(ds, rets, assets, t, dpb, st):
        rebal = max(1, round(5 / dpb))
        if "tr" not in st:
            st["tr"] = [{a: 0.0 for a in assets} for _ in range(rebal)]
        ws, wl, vwin = max(1, round(15 / dpb)), max(2, round(35 / dpb)), max(4, round(20 / dpb))
        if t < wl:
            return {a: 0.0 for a in assets}
        slot = t % rebal
        sec_map = {}
        for a in assets:
            sec_map.setdefault(SECTORS[a], []).append(a)
        active = []
        for _, mem in sec_map.items():
            best = None
            for a in mem:
                m1, m2, v = _mom(ds, a, t, ws), _mom(ds, a, t, wl), _rvol(rets, a, t, vwin, dpb)
                if m1 > 0 and m2 > 0:
                    cand = (abs((m1 + m2) / v), a, +1.0, v)
                elif m1 < 0 and m2 < 0:
                    cand = (abs((m1 + m2) / v), a, -1.0, v)
                else:
                    cand = None
                if cand and (best is None or cand[0] > best[0]):
                    best = cand
            if best:
                active.append((best[1], best[2], best[3]))
        tw = {a: 0.0 for a in assets}
        if active:
            per_v = target_vol / math.sqrt(len(active))
            for a, d, v in active:
                tw[a] = d * min(per_v / v, TAIL_CAPS[a] * cap_mult)
        st["tr"][slot] = tw
        return {a: sum(tr[a] for tr in st["tr"]) / rebal for a in assets}
    return engine


def make_titan_fusion(
    w_ts: float = 0.75,
    w_sp: float = 0.25,
    vol_core: float = 0.0175,
    cap_mult: float = 1.10,
    div_boost: float = 1.15,
    eq_short_mode: str = "bear05",
    metal_short_mode: str = "guard90",
    fast_d: int = 15,
    slow_d: int = 35,
):
    """
    Strategy #1 (SOVEREIGN-TITAN-MAX): eq_short_mode='bear05', metal_short_mode='guard90'
    Strategy #2 (SOVEREIGN-TITAN-7)  : eq_short_mode='none',   metal_short_mode='none'
    """
    def engine(ds, rets, assets, t, dpb, st):
        rebal = max(1, round(5 / dpb))
        if "tr_ts" not in st:
            st["tr_ts"] = [{a: 0.0 for a in assets} for _ in range(rebal)]
            st["tr_sp"] = [{a: 0.0 for a in assets} for _ in range(rebal)]
        ws, wl, vwin = max(1, round(fast_d / dpb)), max(2, round(slow_d / dpb)), max(4, round(20 / dpb))
        if t < wl:
            return {a: 0.0 for a in assets}
        slot = t % rebal

        # Engine 1: Sector-Best Dual-Horizon TSMOM
        sec_map = {}
        for a in assets:
            sec_map.setdefault(SECTORS[a], []).append(a)
        active = []
        for sec, mem in sec_map.items():
            best = None
            for a in mem:
                m1, m2, v = _mom(ds, a, t, ws), _mom(ds, a, t, wl), _rvol(rets, a, t, vwin, dpb)
                d = 0.0
                if m1 > 0 and m2 > 0:
                    d = +1.0
                elif m1 < 0 and m2 < 0:
                    ok = True
                    if sec == "EQUITY":
                        ok = _allow_short(ds, a, t, dpb, eq_short_mode)
                    elif sec == "METALS":
                        ok = _allow_short(ds, a, t, dpb, metal_short_mode)
                    if ok:
                        d = -1.0
                if d != 0.0:
                    cand = (abs((m1 + m2) / v), a, d, v)
                    if best is None or cand[0] > best[0]:
                        best = cand
            if best:
                active.append((best[1], best[2], best[3]))
        tw_ts = {a: 0.0 for a in assets}
        if active:
            per_v = vol_core / math.sqrt(len(active))
            for a, d, v in active:
                tw_ts[a] = d * min(per_v / v, TAIL_CAPS[a] * cap_mult)
        st["tr_ts"][slot] = tw_ts
        w1 = {a: sum(tr[a] for tr in st["tr_ts"]) / rebal for a in assets}

        # Engine 2: Signed Cross-Sector Dispersion
        ws_sp, wl_sp = max(1, round(20 / dpb)), max(2, round(30 / dpb))
        scores = []
        for a in assets:
            m = 0.5 * _mom(ds, a, t, ws_sp) + 0.5 * _mom(ds, a, t, wl_sp)
            v = _rvol(rets, a, t, vwin, dpb)
            scores.append((m / v, a, m, v))
        scores.sort(reverse=True)

        longs, ul = [], set()
        for _, a, m, v in scores:
            if len(longs) >= 2:
                break
            if SECTORS[a] in ul or m <= 0:
                continue
            longs.append((a, v))
            ul.add(SECTORS[a])

        ls = {a for a, _ in longs}
        shorts, us = [], set()
        for _, a, m, v in reversed(scores):
            if len(shorts) >= 2:
                break
            if a in ls or SECTORS[a] in us or m >= 0:
                continue
            if SECTORS[a] == "EQUITY" and not _allow_short(ds, a, t, dpb, eq_short_mode):
                continue
            if SECTORS[a] == "METALS" and not _allow_short(ds, a, t, dpb, metal_short_mode):
                continue
            shorts.append((a, v))
            us.add(SECTORS[a])

        tw_sp = {a: 0.0 for a in assets}
        n_legs = len(longs) + len(shorts)
        if n_legs > 0:
            per_v = vol_core / math.sqrt(n_legs)
            for a, v in longs:
                tw_sp[a] = min(per_v / v, TAIL_CAPS[a] * cap_mult)
            for a, v in shorts:
                tw_sp[a] = -min(per_v / v, TAIL_CAPS[a] * cap_mult)
        st["tr_sp"][slot] = tw_sp
        w2 = {a: sum(tr[a] for tr in st["tr_sp"]) / rebal for a in assets}

        comb = {}
        for a in assets:
            raw = (w_ts * w1[a] + w_sp * w2[a]) * div_boost
            cap = TAIL_CAPS[a] * cap_mult
            comb[a] = max(-cap, min(cap, raw))
        return comb
    return engine


STRATEGY_REGISTRY = {
    "SOVEREIGN-TITAN-MAX": lambda risk_mode="funded": make_titan_fusion(
        vol_core=0.0155 if risk_mode == "eval" else 0.0175,
        eq_short_mode="bear05",
        metal_short_mode="guard90",
    ),
    "SOVEREIGN-TITAN-7": lambda risk_mode="funded": make_titan_fusion(
        vol_core=0.0155 if risk_mode == "eval" else 0.0175,
        eq_short_mode="none",
        metal_short_mode="none",
    ),
    "SEC-TSMOM-4": lambda risk_mode="funded": make_sec_tsmom_4(
        target_vol=0.0125 if risk_mode == "eval" else 0.0140,
        cap_mult=0.95,
    ),
}


def get_live_target_weights(
    strategy_name: str,
    price_history: Dict[str, List[float]],
    current_drawdown: float = 0.0,
    intraday_pnl_pct: float = 0.0,
    risk_mode: str = "funded",
) -> Dict[str, float]:
    """
    Unified entry point for live/paper execution across all Top 3 strategies.
    Requires >= 95 daily closes per symbol in price_history.
    """
    assets = [a for a in price_history.keys() if a in SECTORS]
    n = len(price_history[assets[0]])
    rets = {a: [0.0] + [price_history[a][i] / price_history[a][i - 1] - 1.0 for i in range(1, n)] for a in assets}
    eng = STRATEGY_REGISTRY[strategy_name](risk_mode=risk_mode)
    st = {}
    w = {a: 0.0 for a in assets}
    for t in range(n):
        w = eng(price_history, rets, assets, t, 1.0, st)
    return apply_prop_shield(w, current_drawdown=current_drawdown, intraday_pnl_pct=intraday_pnl_pct)
