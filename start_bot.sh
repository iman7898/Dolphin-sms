#!/data/data/com.termux/files/usr/bin/bash
# 🤖 راه‌اندازی Bot Worker
cd ~/otp_panel
pkill -f bot_worker.py
sleep 1
nohup python3 bot_worker.py > bot.log 2>&1 &
sleep 2
echo "✅ Bot worker راه‌اندازی شد"
tail -10 bot.log
