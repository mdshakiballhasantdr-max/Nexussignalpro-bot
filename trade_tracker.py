"""
প্রতিটা পাঠানো সিগন্যালকে একটা ট্রেড হিসেবে ট্র্যাক করে রাখে।
TP/SL hit হলে রেজাল্ট performance_log.csv-তে লগ হয় — এতে বট নিজের সত্যিকারের
পারফরম্যান্স/উইনরেট নিজেই হিসেব করতে পারে এবং আপনি চাইলে যেকোনো সময় CSV
ফাইলটা Excel/Google Sheets-এ খুলে নিজে অডিট করতে পারবেন।

TP1 hit হলে SL breakeven-এ সরানো হয় (professional risk management) এবং
TP2-এর জন্য ট্রেড চালু থাকে।
"""

import json
import os
import csv
from datetime import datetime

OPEN_TRADES_FILE = "open_trades.json"
PERFORMANCE_LOG_FILE = "performance_log.csv"


def load_open_trades():
    if not os.path.exists(OPEN_TRADES_FILE):
        return []
    with open(OPEN_TRADES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_open_trades(trades):
    with open(OPEN_TRADES_FILE, "w", encoding="utf-8") as f:
        json.dump(trades, f, indent=2, ensure_ascii=False)


def has_open_trade(trades, symbol):
    return any(t["symbol"] == symbol for t in trades)


def open_trade(trades, symbol, signal):
    trade = {
        "symbol": symbol,
        "direction": signal["direction"],
        "entry": signal["entry"],
        "sl": signal["sl"],
        "initial_sl": signal["sl"],  # breakeven-এ সরানোর পরও আসল রিস্ক মনে রাখার জন্য
        "tp1": signal["tp1"],
        "tp2": signal["tp2"],
        "tp1_hit": False,
        "opened_at": datetime.now().isoformat(timespec="seconds"),
    }
    trades.append(trade)
    save_open_trades(trades)
    return trade


def log_performance(trade, result, exit_price):
    file_exists = os.path.exists(PERFORMANCE_LOG_FILE)
    base_risk = abs(trade["entry"] - trade["initial_sl"])

    r_multiple = 0.0
    if base_risk > 0:
        if trade["direction"] == "BUY":
            r_multiple = (exit_price - trade["entry"]) / base_risk
        else:
            r_multiple = (trade["entry"] - exit_price) / base_risk

    with open(PERFORMANCE_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "symbol", "direction", "entry", "sl", "tp1", "tp2",
                "result", "exit_price", "r_multiple", "opened_at", "closed_at",
            ])
        writer.writerow([
            trade["symbol"], trade["direction"], trade["entry"], trade["sl"],
            trade["tp1"], trade["tp2"], result, exit_price, round(r_multiple, 2),
            trade["opened_at"], datetime.now().isoformat(timespec="seconds"),
        ])


def check_trade(trade, current_price):
    """
    বর্তমান প্রাইসের সাথে মিলিয়ে দেখে SL/TP1/TP2 hit হয়েছে কিনা।
    রিটার্ন করে: None (এখনো চলছে), "tp1", "tp2", বা "sl"
    """
    if trade["direction"] == "BUY":
        if current_price <= trade["sl"]:
            return "sl"
        if not trade["tp1_hit"] and current_price >= trade["tp1"]:
            return "tp1"
        if trade["tp1_hit"] and current_price >= trade["tp2"]:
            return "tp2"
    else:
        if current_price >= trade["sl"]:
            return "sl"
        if not trade["tp1_hit"] and current_price <= trade["tp1"]:
            return "tp1"
        if trade["tp1_hit"] and current_price <= trade["tp2"]:
            return "tp2"
    return None


def get_today_stats():
    if not os.path.exists(PERFORMANCE_LOG_FILE):
        return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "total_r": 0.0}

    today = datetime.now().date().isoformat()
    total = wins = losses = 0
    total_r = 0.0
    with open(PERFORMANCE_LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["closed_at"].startswith(today):
                total += 1
                total_r += float(row["r_multiple"])
                if row["result"] in ("tp1", "tp2") or float(row["r_multiple"]) > 0:
                    wins += 1
                else:
                    losses += 1
    win_rate = (wins / total * 100) if total else 0.0
    return {"total": total, "wins": wins, "losses": losses, "win_rate": win_rate, "total_r": total_r}
