"""
পুরো SMC/ICT মডেল একসাথে — "Power of Three" পদ্ধতি (pure Python, pandas ছাড়া)।
"""

from market_structure import find_swings, get_market_structure
from smc_zones import (
    detect_liquidity_sweep,
    confirm_choch,
    find_order_block,
    find_fair_value_gap,
    find_next_liquidity_target,
)
from killzones import in_killzone, current_session_name
from volatility import atr


def generate_signal(candles_h1, candles_m15, config):
    lookback = config.get("swing_lookback", 3)

    h1_s = find_swings(candles_h1, lookback)
    structure = get_market_structure(h1_s)
    if structure == "neutral":
        return None
    direction = structure

    sweep = detect_liquidity_sweep(candles_h1, direction, lookback, search_window=20)
    if sweep is None:
        return None

    choch = confirm_choch(candles_h1, direction, sweep["sweep_index"])
    if choch is None:
        return None

    ob = find_order_block(candles_h1, direction, sweep["sweep_index"], choch["break_index"])
    fvg = find_fair_value_gap(candles_h1, direction, sweep["sweep_index"])

    entry_zone = ob
    last_close = candles_m15[-1]["close"]
    last_open = candles_m15[-1]["open"]

    zone_low, zone_high = entry_zone["low"], entry_zone["high"]
    if not (zone_low <= last_close <= zone_high):
        return None

    if direction == "bullish" and last_close <= last_open:
        return None
    if direction == "bearish" and last_close >= last_open:
        return None

    if config.get("require_killzone", True) and not in_killzone():
        return None

    atr_series = atr(candles_m15)
    atr_val = atr_series[-1] if atr_series else 0
    if atr_val <= 0:
        return None
    buffer = atr_val * config.get("sl_buffer_atr_mult", 0.25)

    entry = last_close
    if direction == "bullish":
        sl = sweep["sweep_low"] - buffer
    else:
        sl = sweep["sweep_high"] + buffer

    risk = abs(entry - sl)
    if risk <= 0:
        return None

    tp1, tp2 = find_next_liquidity_target(candles_h1, direction, entry, lookback)
    min_rr = config.get("min_risk_reward", 2.0)
    if tp1 is None:
        tp1 = entry + risk * min_rr if direction == "bullish" else entry - risk * min_rr
        tp2 = entry + risk * min_rr * 1.5 if direction == "bullish" else entry - risk * min_rr * 1.5

    reward = abs(tp1 - entry)
    if reward / risk < min_rr:
        return None

    reasons = [
        f"H1 structure: {direction.upper()} ({'HH/HL' if direction=='bullish' else 'LH/LL'})",
        f"Liquidity sweep @ {round(sweep['swept_level'], 4)} (stop hunt confirmed)",
        f"CHoCH confirmed @ {round(choch['level'], 4)}",
        "Order Block retest" + (" + Fair Value Gap" if fvg else ""),
        f"M15 confirmation candle ({'bullish' if direction=='bullish' else 'bearish'})",
        f"Session: {current_session_name()}",
    ]

    return {
        "direction": "BUY" if direction == "bullish" else "SELL",
        "entry": round(entry, 4),
        "sl": round(sl, 4),
        "tp1": round(tp1, 4),
        "tp2": round(tp2, 4),
        "reasons": reasons,
        "rr": round(reward / risk, 2),
    }
