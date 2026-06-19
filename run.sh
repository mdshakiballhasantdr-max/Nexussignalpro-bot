#!/data/data/com.termux/files/usr/bin/bash
#
# এই স্ক্রিপ্ট দিয়ে বট চালালে, কোনো কারণে main.py ক্র্যাশ করলেও
# (যেমন অপ্রত্যাশিত এরর, নেটওয়ার্ক সমস্যা ইত্যাদি) এটা ৫ সেকেন্ড পর
# নিজে থেকেই আবার চালু হয়ে যাবে — বট পুরোপুরি বন্ধ হয়ে থাকবে না।
#
# ব্যবহার: bash run.sh   (অথবা: chmod +x run.sh; ./run.sh)
# বন্ধ করতে: Ctrl+C (দুইবার, যদি restart loop-এ থাকে)

cd "$(dirname "$0")"

while true; do
    echo "[$(date)] বট চালু হচ্ছে..."
    python main.py
    EXIT_CODE=$?
    echo "[$(date)] বট বন্ধ হয়ে গেছে (exit code: $EXIT_CODE)। ৫ সেকেন্ড পর আবার চালু হবে।"
    sleep 5
done
