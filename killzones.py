"""
ICT Killzone ফিল্টার — যে সময়গুলোতে institutional volume/liquidity সবচেয়ে বেশি থাকে
বলে ICT মডেলে ধরা হয়। চাইলে config.json-এ require_killzone: false করে বন্ধ রাখা যায়
(বিশেষত BTC ২৪/৭ মার্কেট, তাই killzone ছাড়াও চলতে পারে)।
"""

from datetime import datetime, timezone

LONDON_KZ = (7, 10)    # 07:00-10:00 UTC
NEWYORK_KZ = (12, 15)  # 12:00-15:00 UTC


def in_killzone(now_utc=None) -> bool:
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    h = now_utc.hour
    return (LONDON_KZ[0] <= h < LONDON_KZ[1]) or (NEWYORK_KZ[0] <= h < NEWYORK_KZ[1])


def current_session_name(now_utc=None) -> str:
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    h = now_utc.hour
    if LONDON_KZ[0] <= h < LONDON_KZ[1]:
        return "London Killzone"
    if NEWYORK_KZ[0] <= h < NEWYORK_KZ[1]:
        return "New York Killzone"
    return "Outside Killzone"
