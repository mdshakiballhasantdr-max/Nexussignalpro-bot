# Nexussignalpro_bot — XAUUSD + BTCUSD SMC/ICT Telegram সিগন্যাল বট

বট: **@NexussignalXau_bot**

## সততার সাথে শুরু করি
Order Block, FVG, Liquidity Sweep, CHoCH — এগুলো এখন রিটেইল ট্রেডিং কমিউনিটিতে সবচেয়ে বেশি
আলোচিত কনসেপ্ট, "গোপন প্রাতিষ্ঠানিক ফর্মুলা" নয়। তবে এটা basic indicator bot-এর চেয়ে অনেক বেশি
যৌক্তিক একটা price-action ফ্রেমওয়ার্ক। **কোনো বট ১০০% জেতে না** — রিয়েল মানির আগে demo-তে
যাচাই করুন, প্রতি ট্রেডে ১-২%-এর বেশি রিস্ক নেবেন না।

## এই ভার্সনে কী স্থায়ীভাবে ঠিক হয়েছে
- pandas বাদ — পুরো বট এখন pure Python দিয়ে লেখা, শুধু `requests` লাগে। Termux-এ আর কখনো
  ভারী কম্পাইলেশনের সমস্যায় পড়বেন না, `pip install -r requirements.txt` কয়েক সেকেন্ডে শেষ হবে
- BTC ডেটার ব্যাকআপ — Binance অনুপলব্ধ/ব্লক হলে বট নিজে থেকেই Twelve Data দিয়ে BTC ডেটা
  আনবে (একই Twelve Data key ব্যবহার হয়, নতুন কোনো API key লাগে না)
- Auto-restart — `run.sh` দিয়ে চালালে বট ক্র্যাশ করলেও ৫ সেকেন্ড পর নিজে থেকে আবার চালু হবে

## স্ট্র্যাটেজি মডেল (ICT "Power of Three")
H1 Market Structure → Liquidity Sweep → CHoCH কনফার্মেশন → Order Block/FVG জোনে রিট্রেস →
M15 কনফার্মেশন ক্যান্ডেল → London/NY Killzone ফিল্টার → পরবর্তী liquidity-তে TP, sweep wick-এর
বাইরে SL, ন্যূনতম R:R না মিললে স্কিপ। প্রতিটা সিগন্যাল `performance_log.csv`-তে আসল ফলাফল সহ লগ হয়।

## ধাপ ১: GitHub-এ আপলোড
`config.json`-এ কোনো secret নেই — নিশ্চিন্তে পাবলিক রিপোতে রাখা যায়।
```bash
cd ~/Nexussignalpro_bot
git init
git add .
git commit -m "Nexussignalpro_bot - SMC/ICT signal bot"
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

## ধাপ ২: Termux-এ সেটআপ
**(প্রথমেই, ভবিষ্যতে `pkg install` এরর এড়াতে)** একটা নির্ভরযোগ্য mirror বেছে নিন:
```bash
termux-change-repo
```
(একটা মেনু আসবে — Mirror group থেকে যেকোনো একটা, যেমন `Main repository` সিলেক্ট করুন)

তারপর:
```bash
pkg update -y && pkg upgrade -y
pkg install python git -y
```
আগে থেকে `xau_btc_smc_bot` ফোল্ডার থাকলে নতুন নামে রাখতে:
```bash
mv ~/xau_btc_smc_bot ~/Nexussignalpro_bot
```
নতুন করে নামাতে চাইলে:
```bash
git clone https://github.com/<your-username>/<repo-name>.git ~/Nexussignalpro_bot
cd ~/Nexussignalpro_bot
pip install -r requirements.txt
```
(এখন pandas নেই, তাই এটা কয়েক সেকেন্ডেই শেষ হবে)

## ধাপ ৩: Environment Variables
`~/.bashrc`-তে (আগে থেকে বসানো না থাকলে):
```bash
nano ~/.bashrc
```
```bash
export TELEGRAM_BOT_TOKEN="আপনার_বট_টোকেন"
export TELEGRAM_CHAT_ID="আপনার_চ্যাট_আইডি"
export TWELVE_DATA_API_KEY="আপনার_টুয়েলভ_ডেটা_কী"
```
সেভ করে (`Ctrl+O`, Enter, `Ctrl+X`):
```bash
source ~/.bashrc
```

## ধাপ ৪: BTC-এর জন্য আলাদা কোনো API লাগবে কি?
**না।** BTC ডেটা আসে Binance-এর পাবলিক মার্কেট ডেটা endpoint থেকে, যেখানে কোনো key/login লাগে
না (শুধু account/trading করতে গেলে key লাগে, আমরা শুধু দাম পড়ছি)। আগে থেকে সেট করা
`TWELVE_DATA_API_KEY`-ই BTC-এর ব্যাকআপ হিসেবে কাজ করবে যদি Binance কখনো কাজ না করে —
তাই কিছু নতুন করে যোগ করার দরকার নেই।

## ধাপ ৫: চালান (auto-restart সহ, সুপারিশকৃত)
```bash
cd ~/Nexussignalpro_bot
chmod +x run.sh
bash run.sh
```
(সাধারণ `python main.py`-ও চলবে, কিন্তু `run.sh` ক্র্যাশ হলে নিজে থেকে restart করবে)

## ধাপ ৬: ২৪/৭ চালু রাখা — ভবিষ্যতে বট হঠাৎ বন্ধ হয়ে যাওয়া এড়াতে
তিনটা জিনিস একসাথে করুন:

**ক) Battery optimization বন্ধ করুন** (Android Termux-কে ব্যাকগ্রাউন্ডে মেরে ফেলা বন্ধ করতে):
ফোনের Settings → Apps → Termux → Battery → **Unrestricted/No restrictions** সিলেক্ট করুন
(ফোনভেদে মেনুর নাম একটু আলাদা হতে পারে)

**খ) wake-lock + tmux:**
```bash
termux-wake-lock
pkg install tmux -y
tmux new -s nexus
bash run.sh
```
`Ctrl+B` তারপর `D` চাপুন — ব্যাকগ্রাউন্ডে চলতে থাকবে। ফিরে দেখতে: `tmux attach -t nexus`

**গ) ফোন রিস্টার্ট হলে অটো-স্টার্ট (ঐচ্ছিক):** F-Droid থেকে **Termux:Boot** অ্যাপ ইনস্টল করুন,
তারপর `~/.termux/boot/start-bot.sh` ফাইলে নিচের লাইন লিখে রাখলে ফোন রিস্টার্টের পরও বট নিজে
চালু হয়ে যাবে:
```bash
tmux new -d -s nexus 'bash ~/Nexussignalpro_bot/run.sh'
```

## কনফিগারেশন টিউনিং (`config.json`)
- `require_killzone` (ডিফল্ট `true`): `false` করলে সারাদিন সিগন্যাল আসতে পারবে
- `min_risk_reward` (ডিফল্ট `2.0`)
- `swing_lookback` (ডিফল্ট `3`)
- `sl_buffer_atr_mult` (ডিফল্ট `0.25`)

## অন্যান্য ভবিষ্যৎ সমস্যা ও সমাধান (একবারে)
| সমস্যা | সমাধান |
|---|---|
| `pkg install` এরর / mirror সমস্যা | `termux-change-repo` চালিয়ে নতুন mirror বাছুন |
| বট কিছুক্ষণ পর বন্ধ হয়ে যায় | Battery optimization বন্ধ করুন (ধাপ ৬-ক) |
| Termux বন্ধ করলে বট থেমে যায় | `tmux` ব্যবহার করুন (ধাপ ৬-খ) |
| ফোন রিস্টার্টে বট চালু হয় না | Termux:Boot সেটআপ করুন (ধাপ ৬-গ) |
| `python main.py` ক্র্যাশ করে | `bash run.sh` দিয়ে চালান — অটো-restart হবে |
| Twelve Data রেট লিমিট (800/day) | `signal_check_interval_sec`/`price_check_interval_sec` বাড়ান `config.json`-এ |
| XAUUSD সপ্তাহান্তে সিগন্যাল আসে না | স্বাভাবিক — ফরেক্স মার্কেট শনি-রবি বন্ধ থাকে |
| token/key ভুলবশত কোথাও শেয়ার হলে | সাথে সাথে BotFather/Twelve Data dashboard থেকে revoke + নতুন key বানান |
| GitHub-এ push করলে secret যাচ্ছে কিনা চিন্তা | `config.json`-এ কোনো secret নেই, `.gitignore`-এ `.env` বাদ — নিরাপদ |
