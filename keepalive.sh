#!/data/data/com.termux/files/usr/bin/bash
cd ~/otp_panel
termux-wake-lock

while true; do
    # چک کردن cloudflared
    if ! pgrep -f "cloudflared tunnel" > /dev/null; then
        echo "$(date) - cloudflared مرده، دوباره راه می‌ندازم..."
        nohup cloudflared tunnel --url http://localhost:8080 --no-autoupdate > cloudflare.log 2>&1 &
        sleep 15
        NEW_URL=$(grep -oP "https://[a-z0-9-]+\.trycloudflare\.com" cloudflare.log | head -1)
        if [ -n "$NEW_URL" ]; then
            echo "$NEW_URL" > public_url.txt
            echo "$(date) - URL جدید: $NEW_URL"
        fi
    fi

    # چک کردن پنل
    if ! pgrep -f "python3 app.py" > /dev/null; then
        echo "$(date) - پنل مرده، دوباره..."
        nohup python3 app.py > panel.log 2>&1 &
    fi

    # چک کردن ربات
    if ! pgrep -f bot_runner > /dev/null; then
        echo "$(date) - ربات مرده، دوباره..."
        nohup python3 -u bot_runner.py > bot.log 2>&1 &
    fi

    sleep 30
done
