"""
ATR (Average True Range) — pure Python (pandas/numpy ছাড়া)। SL-এর বাফার
দূরত্ব ঠিক করতে ব্যবহৃত হয়। কোনো সিগন্যাল জেনারেট করে না, শুধু রিস্ক সাইজিং।
"""


def atr(candles, period: int = 14):
    n = len(candles)
    if n == 0:
        return []

    tr_list = [0.0] * n
    for i in range(n):
        h, l = candles[i]["high"], candles[i]["low"]
        if i == 0:
            tr_list[i] = h - l
        else:
            prev_close = candles[i - 1]["close"]
            tr_list[i] = max(h - l, abs(h - prev_close), abs(l - prev_close))

    atr_list = [0.0] * n
    alpha = 1 / period
    atr_list[0] = tr_list[0]
    for i in range(1, n):
        atr_list[i] = tr_list[i] * alpha + atr_list[i - 1] * (1 - alpha)
    return atr_list
