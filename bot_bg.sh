#!/data/data/com.termux/files/usr/bin/bash
cd ~/otp_panel
pkill -f bot_runner.py 2>/dev/null
pkill -f bot_worker.py 2>/dev/null
sleep 1
nohup python3 bot_runner.py > bot_runner.log 2>&1 &
sleep 1
nohup python3 bot_worker.py > bot_worker.log 2>&1 &
sleep 2
echo "✅ اجرا شد"
echo "───── آخرین لاگ ─────"
tail -10 bot_runner.log
