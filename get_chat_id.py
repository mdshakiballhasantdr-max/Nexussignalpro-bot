"""
chat_id খুঁজে বের করার জন্য একবার-চালানো হেল্পার স্ক্রিপ্ট।

ব্যবহার:
1. টেলিগ্রামে আপনার বট খুঁজে বের করে তাকে যেকোনো একটা মেসেজ পাঠান (যেমন: "hi")।
2. Termux-এ এই env var সেট করুন: export TELEGRAM_BOT_TOKEN=আপনার_টোকেন
3. রান করুন: python get_chat_id.py
4. টার্মিনালে আপনার chat_id দেখাবে — সেটা TELEGRAM_CHAT_ID env var হিসেবে সেট করুন।
"""

import os
import sys
from telegram_bot import get_updates

token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    sys.exit("❌ TELEGRAM_BOT_TOKEN env var সেট নেই। আগে: export TELEGRAM_BOT_TOKEN=আপনার_টোকেন")

data = get_updates(token)

if not data or not data.get("result"):
    print("কোনো মেসেজ পাওয়া যায়নি। আগে বটকে টেলিগ্রামে একটা মেসেজ পাঠান, তারপর আবার এই স্ক্রিপ্ট রান করুন।")
else:
    seen = set()
    for update in data["result"]:
        msg = update.get("message") or update.get("channel_post")
        if not msg:
            continue
        chat = msg["chat"]
        cid = chat["id"]
        if cid not in seen:
            seen.add(cid)
            name = chat.get("title") or chat.get("username") or chat.get("first_name")
            print(f"chat_id: {cid}   ({name})")
