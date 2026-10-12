#!/data/data/com.termux/files/usr/bin/bash
cd ~/otp_panel

pkill -9 -f "python3 app.py" 2>/dev/null
pkill -9 -f bot_runner 2>/dev/null
pkill -9 -f cloudflared 2>/dev/null
sleep 1

echo "📡 پنل..."
nohup python3 app.py > panel.log 2>&1 &
sleep 4

echo "🌐 تونل عمومی..."
rm -f cloudflare.log
nohup cloudflared tunnel --url http://localhost:8080 --no-autoupdate > cloudflare.log 2>&1 &
sleep 15

URL=$(grep -oP "https://[a-z0-9-]+\.trycloudflare\.com" cloudflare.log | head -1)
[ -z "$URL" ] && sleep 10 && URL=$(grep -oP "https://[a-z0-9-]+\.trycloudflare\.com" cloudflare.log | head -1)

if [ -n "$URL" ]; then
    echo "$URL" > public_url.txt
    echo ""
    echo "=========================================="
    echo "✅ پنل عمومی آماده شد!"
    echo ""
    echo "🌐 لینک‌ها:"
    echo "  🔐 ادمین:     $URL/admin/login"
    echo "  🏪 مغازه‌دار: $URL/panel/login"
    echo "  🛒 مشتری:     $URL/customer"
    echo "=========================================="
else
    echo "❌ خطا. لاگ:"
    tail -15 cloudflare.log
fi

echo "🤖 ربات..."
nohup python3 -u bot_runner.py > bot.log 2>&1 &
sleep 3
