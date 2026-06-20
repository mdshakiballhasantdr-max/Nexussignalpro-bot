""" SMC/ICT স্ট্র্যাটেজির ঐতিহাসিক ডেটার ওপর ব্যাকটেস্ট। এটা লাইভ ট্রেডিং করে না, কোনো Telegram মেসেজও পাঠায় না — শুধু অতীতের ডেটায় স্ট্র্যাটেজি চালিয়ে দেখায় তখন কেমন ফলাফল আসত। প্রতিটা মুহূর্তে শুধু সেই মুহূর্ত পর্যন্ত যা ডেটা "জানা ছিল" তা দিয়েই সিদ্ধান্ত নেওয়া হয় (no lookahead bias)। চালানো: python backtest.py ফলাফল কনসোলে দেখাবে + backtest_results.csv-তে প্রতিটা ট্রেডের বিস্তারিত সেভ হবে। ⚠️ এটা অতীতের ফলাফল — ভবিষ্যতের গ্যারান্টি না। স্প্রেড/কমিশন/স্লিপেজ হিসাবে ধরা হয়নি, তাই বাস্তব ফলাফল এখানের চেয়ে কিছুটা খারাপ হতে পারে। """

import csv
import json
import os
from datetime import datetime, timezone

from data_fetcher import fetch_candles
from smc_strategy import generate_signal
from tier_b_strategy import generate_tier_b_signal

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

TD_KEY = os.environ.get("TWELVE_DATA_API_KEY")
if not TD_KEY:
    raise SystemExit(
        "TWELVE_DATA_API_KEY env var সেট নেই। আগে: export TWELVE_DATA_API_KEY=আপনার_কী"
    )

SYMBOLS = CONFIG["symbols"]

# ব্যাকটেস্টের জন্য কত ইতিহাস আনা হবে (live bot-এর limit থেকে আলাদা, বেশি লাগে)
M15_LOOKBACK = 1500  # আনুমানিক ১৫-১৬ দিনের M15 ডেটা
H1_LOOKBACK = 1200   # আনুমানিক ৫০ দিনের H1 ডেটা (M15 সময়সীমা ঢাকতে পর্যাপ্ত)

WARMUP_M15 = 30
WARMUP_H1 = 60


def check_candle_against_position(pos, candle):
    """ রক্ষণশীল ধারণা: একই ক্যান্ডেলে SL আর TP দুটোতেই touch করলে SL আগে ধরা হয় (বাস্তবে কোনটা আগে ঘটেছে জানা যায় না, তাই কম-আশাবাদী দিকেই থাকা ভালো)। """
    if pos["direction"] == "BUY":
        if candle["low"] <= pos["sl"]:
            return "sl"
        if not pos["tp1_hit"] and candle["high"] >= pos["tp1"]:
            return "tp1"
        if pos["tp1_hit"] and candle["high"] >= pos["tp2"]:
            return "tp2"
    else:
        if candle["high"] >= pos["sl"]:
            return "sl"
        if not pos["tp1_hit"] and candle["low"] <= pos["tp1"]:
            return "tp1"
        if pos["tp1_hit"] and candle["low"] <= pos["tp2"]:
            return "tp2"
    return None


def simulate_symbol(symbol, symbol_cfg):
    print(f"\n=== {symbol_cfg['display']} ব্যাকটেস্ট শুরু ===")
    h1 = fetch_candles(symbol_cfg, "1h", TD_KEY, limit=H1_LOOKBACK)
    m15 = fetch_candles(symbol_cfg, "15min", TD_KEY, limit=M15_LOOKBACK)
    if not h1 or not m15:
        print("ডেটা আনা যায়নি, এই সিম্বল স্কিপ করা হলো।")
        return []

    trades = []
    open_pos = None
    h1_ptr = 0

    for i in range(WARMUP_M15, len(m15)):
        candle = m15[i]
        t = candle["time"]

        while h1_ptr < len(h1) and h1[h1_ptr]["time"] <= t:
            h1_ptr += 1
        h1_slice = h1[:h1_ptr]

        if len(h1_slice) < WARMUP_H1:
            continue

        if open_pos:
            status = check_candle_against_position(open_pos, candle)
            if status == "tp1":
                open_pos["tp1_hit"] = True
                open_pos["sl"] = open_pos["entry"]  # breakeven
            elif status in ("sl", "tp2"):
                exit_price = open_pos["sl"] if status == "sl" else open_pos["tp2"]
                risk = abs(open_pos["entry"] - open_pos["initial_sl"])
                if risk > 0:
                    if open_pos["direction"] == "BUY":
                        r_mult = (exit_price - open_pos["entry"]) / risk
                    else:
                        r_mult = (open_pos["entry"] - exit_price) / risk
                else:
                    r_mult = 0.0
                trades.append({
                    "symbol": symbol,
                    "tier": open_pos.get("tier", "A"),
                    "direction": open_pos["direction"],
                    "entry": round(open_pos["entry"], 4),
                    "result": status,
                    "r_multiple": round(r_mult, 2),
                    "opened_at": open_pos["opened_at"],
                    "closed_at": datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                })
                open_pos = None
            continue

        m15_slice = m15[: i + 1]
        try:
            signal = generate_signal(h1_slice, m15_slice, CONFIG)
            if signal is None:
                signal = generate_tier_b_signal(h1_slice, m15_slice, CONFIG)
        except Exception as e:
            print(f"[backtest] স্ট্র্যাটেজি এরর: {e}")
            signal = None

        if signal:
            open_pos = {
                "tier": signal.get("tier", "A"),
                "direction": signal["direction"],
                "entry": signal["entry"],
                "sl": signal["sl"],
                "initial_sl": signal["sl"],
                "tp1": signal["tp1"],
                "tp2": signal["tp2"],
                "tp1_hit": False,
                "opened_at": datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
            }

    return trades


def print_report(all_trades):
    if not all_trades:
        print("\nকোনো ট্রেড সিগন্যাল পাওয়া যায়নি এই সময়সীমায়। 'config.json'-এ "
              "min_confluence/require_killzone শিথিল করে আবার চেষ্টা করতে পারেন।")
        return

    def stats_for(trades):
        total = len(trades)
        wins = sum(1 for t in trades if t["r_multiple"] > 0)
        losses = total - wins
        total_r = sum(t["r_multiple"] for t in trades)
        win_rate = (wins / total * 100) if total else 0.0
        avg_r = (total_r / total) if total else 0.0
        gross_win = sum(t["r_multiple"] for t in trades if t["r_multiple"] > 0)
        gross_loss = abs(sum(t["r_multiple"] for t in trades if t["r_multiple"] < 0))
        pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
        return total, wins, losses, win_rate, total_r, avg_r, pf

    print("\n" + "=" * 44)
    print("ব্যাকটেস্ট ফলাফল")
    print("=" * 44)

    for sym in sorted(set(t["symbol"] for t in all_trades)):
        sym_trades = [t for t in all_trades if t["symbol"] == sym]
        total, wins, losses, win_rate, total_r, avg_r, pf = stats_for(sym_trades)
        print(f"\n--- {sym} (Tier A+B মিলিয়ে) ---")
        print(f"মোট ট্রেড: {total}")
        print(f"Win / Loss: {wins} / {losses}")
        print(f"Win rate: {win_rate:.1f}%")
        print(f"মোট R: {total_r:.2f}R")
        print(f"গড় R/ট্রেড: {avg_r:.2f}R")
        print(f"Profit factor: {pf:.2f}")

        for tier in ("A", "B"):
            tier_trades = [t for t in sym_trades if t.get("tier", "A") == tier]
            if not tier_trades:
                continue
            tt_, tw, tl, twr, ttr, tar, tpf = stats_for(tier_trades)
            print(f" Tier {tier}: {tt_} ট্রেড, win rate {twr:.1f}%, মোট {ttr:.2f}R")

    total, wins, losses, win_rate, total_r, avg_r, pf = stats_for(all_trades)
    print("\n--- সব মিলিয়ে (XAUUSD+BTCUSD, Tier A+B) ---")
    print(f"মোট ট্রেড: {total}")
    print(f"Win / Loss: {wins} / {losses}")
    print(f"Win rate: {win_rate:.1f}%")
    print(f"মোট R: {total_r:.2f}R")
    print(f"গড় R/ট্রেড: {avg_r:.2f}R")
    print(f"Profit factor: {pf:.2f}")
    print("=" * 44)

    with open("backtest_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["symbol", "tier", "direction", "entry", "result", "r_multiple", "opened_at", "closed_at"]
        )
        writer.writeheader()
        for t in all_trades:
            writer.writerow(t)
    print("\nবিস্তারিত প্রতিটা ট্রেড সেভ হয়েছে: backtest_results.csv")
    print("⚠️ স্প্রেড/কমিশন/স্লিপেজ হিসাবে নেই — বাস্তব ফলাফল এর চেয়ে কিছুটা কম হতে পারে।")


def main():
    all_trades = []
    for symbol, symbol_cfg in SYMBOLS.items():
        trades = simulate_symbol(symbol, symbol_cfg)
        print(f"{symbol}: {len(trades)}টা ট্রেড পাওয়া গেছে এই সময়সীমায়")
        all_trades.extend(trades)
    print_report(all_trades)


if __name__ == "__main__":
    main()
