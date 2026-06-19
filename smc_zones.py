"""
SMC/ICT কোর কনসেপ্ট ডিটেকশন (pure Python, pandas/numpy ছাড়া):
- liquidity sweep, CHoCH, order block, fair value gap, next liquidity target
"""

from market_structure import find_swings


def detect_liquidity_sweep(candles, direction, lookback=3, search_window=15):
    candles = find_swings(candles, lookback)
    n = len(candles)
    start = max(0, n - search_window)

    if direction == "bullish":
        swing_lows = [(i, c["low"]) for i, c in enumerate(candles) if c["swing_low"]]
        if len(swing_lows) < 2:
            return None
        ref_idx, ref_level = swing_lows[-2]
        for i in range(max(ref_idx + 1, start), n):
            if candles[i]["low"] < ref_level and candles[i]["close"] > ref_level:
                return {
                    "swept_level": ref_level,
                    "sweep_index": i,
                    "sweep_low": candles[i]["low"],
                    "sweep_high": candles[i]["high"],
                }
        return None
    else:
        swing_highs = [(i, c["high"]) for i, c in enumerate(candles) if c["swing_high"]]
        if len(swing_highs) < 2:
            return None
        ref_idx, ref_level = swing_highs[-2]
        for i in range(max(ref_idx + 1, start), n):
            if candles[i]["high"] > ref_level and candles[i]["close"] < ref_level:
                return {
                    "swept_level": ref_level,
                    "sweep_index": i,
                    "sweep_low": candles[i]["low"],
                    "sweep_high": candles[i]["high"],
                }
        return None


def confirm_choch(candles, direction, sweep_index, lookback_ref=2):
    n = len(candles)
    if direction == "bullish":
        window = candles[max(0, sweep_index - lookback_ref): sweep_index + 1]
        ref_high = max(c["high"] for c in window)
        for i in range(sweep_index + 1, n):
            if candles[i]["close"] > ref_high:
                return {"break_index": i, "level": ref_high}
        return None
    else:
        window = candles[max(0, sweep_index - lookback_ref): sweep_index + 1]
        ref_low = min(c["low"] for c in window)
        for i in range(sweep_index + 1, n):
            if candles[i]["close"] < ref_low:
                return {"break_index": i, "level": ref_low}
        return None


def find_order_block(candles, direction, sweep_index, break_index):
    rng = range(break_index - 1, sweep_index - 1, -1)
    if direction == "bullish":
        for i in rng:
            if candles[i]["close"] < candles[i]["open"]:
                return {"low": candles[i]["low"], "high": candles[i]["high"], "index": i}
    else:
        for i in rng:
            if candles[i]["close"] > candles[i]["open"]:
                return {"low": candles[i]["low"], "high": candles[i]["high"], "index": i}
    return {
        "low": candles[sweep_index]["low"],
        "high": candles[sweep_index]["high"],
        "index": sweep_index,
    }


def find_fair_value_gap(candles, direction, after_index):
    n = len(candles)
    best = None
    for i in range(max(1, after_index), n - 1):
        if direction == "bullish":
            if candles[i + 1]["low"] > candles[i - 1]["high"]:
                best = {"low": candles[i - 1]["high"], "high": candles[i + 1]["low"], "index": i}
        else:
            if candles[i + 1]["high"] < candles[i - 1]["low"]:
                best = {"low": candles[i + 1]["high"], "high": candles[i - 1]["low"], "index": i}
    return best


def find_next_liquidity_target(candles, direction, entry_price, lookback=3):
    candles_s = find_swings(candles, lookback)
    if direction == "bullish":
        targets = [c["high"] for c in candles_s if c["swing_high"] and c["high"] > entry_price]
        if not targets:
            return None, None
        targets.sort()
        tp1 = targets[0]
        tp2 = targets[1] if len(targets) > 1 else tp1 + (tp1 - entry_price) * 0.5
        return tp1, tp2
    else:
        targets = [c["low"] for c in candles_s if c["swing_low"] and c["low"] < entry_price]
        if not targets:
            return None, None
        targets.sort(reverse=True)
        tp1 = targets[0]
        tp2 = targets[1] if len(targets) > 1 else tp1 - (entry_price - tp1) * 0.5
        return tp1, tp2
