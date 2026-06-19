"""
মূল বট লুপ (SMC/ICT ভার্সন) — Termux-এ ব্যাকগ্রাউন্ডে চালানোর জন্য।
চালানো: python main.py

Secrets (token/key) এখানে config.json থেকে আসে না — environment variable থেকে আসে,
যাতে config.json পুরোপুরি নিরাপদভাবে GitHub-এ রাখা যায় (কোনো secret থাকে না)।
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TWELVE_DATA_API_KEY — এই তিনটা env var
Termux-এ সেট করা থাকতে হবে (README.md দেখুন)।
"""

import json
import os
import sys
import time
from datetime import datetime

from data_fetcher import fetch_candles, fetch_price
from smc_strategy import generate_signal
from telegram_bot import send_message
import trade_tracker as tt

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TD_KEY = os.environ.get("TWELVE_DATA_API_KEY")

if not TOKEN or not CHAT_ID or not TD_KEY:
    sys.exit(
        "❌ Environment variable পাওয়া যায়নি।\n"
        "Termux-এ এগুলো সেট করুন (README.md-এর 'Environment Variables' অংশ দেখুন):\n"
        "  export TELEGRAM_BOT_TOKEN=...\n"
        "  export TELEGRAM_CHAT_ID=...\n"
        "  export TWELVE_DATA_API_KEY=...\n"
        "তারপর আবার চালান: python main.py"
    )

SYMBOLS = CONFIG["symbols"]


def format_signal_message(symbol_display, signal):
    arrow = "🟢 BUY" if signal["direction"] == "BUY" else "🔴 SELL"
    reasons_text = "\n".join(f"  ✓ {r}" for r in signal["reasons"])
    return (
        f"<b>{symbol_display}</b> — SMC/ICT Signal\n"
        f"{arrow}  (R:R {signal['rr']})\n\n"
        f"Entry: <b>{signal['entry']}</b>\n"
        f"SL: {signal['sl']}\n"
        f"TP1: {signal['tp1']}  (breakeven trigger)\n"
        f"TP2: {signal['tp2']}  (runner target)\n\n"
        f"Confluence:\n{reasons_text}\n\n"
        f"⚠️ নিজের রিস্ক ম্যানেজমেন্ট মেনে ট্রেড করুন। এটা আর্থিক পরামর্শ নয়।"
    )


def handle_trade_tracking():
    trades = tt.load_open_trades()
    if not trades:
        return
    changed = False
    remaining = []

    for trade in trades:
        symbol_cfg = SYMBOLS[trade["symbol"]]
        price = fetch_price(symbol_cfg, TD_KEY)
        if price is None:
            remaining.append(trade)
            continue

        status = tt.check_trade(trade, price)

        if status == "sl":
            tt.log_performance(trade, "sl", price)
            label = "Breakeven-এ ক্লোজ (TP1-এর পর SL hit)" if trade["tp1_hit"] else "❌ SL HIT"
            send_message(TOKEN, CHAT_ID, f"{label}\n{trade['symbol']} {trade['direction']} বন্ধ হয়েছে @ {price}")
            changed = True
            continue

        if status == "tp1":
            trade["tp1_hit"] = True
            trade["sl"] = trade["entry"]
            send_message(
                TOKEN, CHAT_ID,
                f"✅ TP1 HIT — {trade['symbol']} {trade['direction']} @ {price}\n"
                f"SL breakeven-এ সরানো হলো। TP2 (runner)-এর জন্য চলছে।",
            )
            changed = True
            remaining.append(trade)
            continue

        if status == "tp2":
            tt.log_performance(trade, "tp2", price)
            send_message(TOKEN, CHAT_ID, f"🎯 TP2 HIT — {trade['symbol']} {trade['direction']} সম্পূর্ণ ক্লোজ @ {price}")
            changed = True
            continue

        remaining.append(trade)

    if changed:
        tt.save_open_trades(remaining)


def handle_signal_generation():
    trades = tt.load_open_trades()
    for symbol, symbol_cfg in SYMBOLS.items():
        if tt.has_open_trade(trades, symbol):
            continue

        df_h1 = fetch_candles(symbol_cfg, "1h", TD_KEY, limit=250)
        df_m15 = fetch_candles(symbol_cfg, "15min", TD_KEY, limit=250)
        if df_h1 is None or df_m15 is None or len(df_h1) < 60 or len(df_m15) < 10:
            continue

        try:
            signal = generate_signal(df_h1, df_m15, CONFIG)
        except Exception as e:
            print(f"[main] Strategy error for {symbol}: {e}")
            continue

        if signal is None:
            continue

        tt.open_trade(trades, symbol, signal)
        msg = format_signal_message(symbol_cfg["display"], signal)
        send_message(TOKEN, CHAT_ID, msg)
        print(f"[{datetime.now()}] Signal sent: {symbol} {signal['direction']}")


_last_summary_date = None


def maybe_send_daily_summary():
    global _last_summary_date
    now = datetime.now()
    if (
        now.hour == CONFIG["daily_summary_hour"]
        and now.minute >= CONFIG["daily_summary_minute"]
        and _last_summary_date != now.date()
    ):
        stats = tt.get_today_stats()
        msg = (
            f"📊 <b>আজকের সামারি</b>\n"
            f"মোট ক্লোজড ট্রেড: {stats['total']}\n"
            f"✅ Win: {stats['wins']}   ❌ Loss: {stats['losses']}\n"
            f"Win rate: {stats['win_rate']:.1f}%\n"
            f"মোট R: {stats['total_r']:.2f}R"
        )
        send_message(TOKEN, CHAT_ID, msg)
        _last_summary_date = now.date()


def main():
    send_message(TOKEN, CHAT_ID, "🤖 XAUUSD/BTCUSD SMC/ICT সিগন্যাল বট চালু হয়েছে।")
    last_price_check = 0
    last_signal_scan = 0

    while True:
        now = time.time()
        try:
            if now - last_price_check >= CONFIG["price_check_interval_sec"]:
                handle_trade_tracking()
                last_price_check = now

            if now - last_signal_scan >= CONFIG["signal_check_interval_sec"]:
                handle_signal_generation()
                last_signal_scan = now

            maybe_send_daily_summary()

        except Exception as e:
            print(f"[main] Loop error: {e}")

        time.sleep(10)


if __name__ == "__main__":
    main()
