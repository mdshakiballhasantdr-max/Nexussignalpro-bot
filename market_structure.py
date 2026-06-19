"""
Market Structure মডিউল — pure price action, pure Python (pandas/numpy ছাড়া)।

- swing high/low: fractal পদ্ধতিতে
- market structure: HH/HL (bullish) বা LH/LL (bearish)
- CHoCH সম্ভাব্য রিভার্সালের সংকেত
"""


def find_swings(candles, lookback: int = 3):
    candles = [dict(c) for c in candles]  # মূল লিস্ট mutate না করার জন্য কপি
    n = len(candles)
    for c in candles:
        c["swing_high"] = False
        c["swing_low"] = False

    for i in range(lookback, n - lookback):
        window = candles[i - lookback: i + lookback + 1]
        hi, lo = candles[i]["high"], candles[i]["low"]
        if hi == max(c["high"] for c in window):
            candles[i]["swing_high"] = True
        if lo == min(c["low"] for c in window):
            candles[i]["swing_low"] = True
    return candles


def get_market_structure(candles) -> str:
    """
    রিটার্ন করে: 'bullish', 'bearish', বা 'neutral'

    সবচেয়ে সাম্প্রতিক swing high/low নিজেই liquidity sweep হতে পারে, তাই
    "established" structure বোঝার জন্য যথাসম্ভব দ্বিতীয়-সাম্প্রতিক জোড়া
    ব্যবহার করা হয়।
    """
    swing_highs = [(i, c["high"]) for i, c in enumerate(candles) if c["swing_high"]]
    swing_lows = [(i, c["low"]) for i, c in enumerate(candles) if c["swing_low"]]

    if len(swing_highs) >= 3 and len(swing_lows) >= 3:
        h_prev, h_last = swing_highs[-3][1], swing_highs[-2][1]
        l_prev, l_last = swing_lows[-3][1], swing_lows[-2][1]
    elif len(swing_highs) >= 2 and len(swing_lows) >= 2:
        h_prev, h_last = swing_highs[-2][1], swing_highs[-1][1]
        l_prev, l_last = swing_lows[-2][1], swing_lows[-1][1]
    else:
        return "neutral"

    if h_last > h_prev and l_last > l_prev:
        return "bullish"
    if h_last < h_prev and l_last < l_prev:
        return "bearish"
    return "neutral"
