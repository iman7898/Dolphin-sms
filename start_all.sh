#!/data/data/com.termux/files/usr/bin/bash
cd ~/otp_panel

echo "🚀 شروع راه‌اندازی..."
echo ""

# ۱) بستن پروسه‌های قبلی
pkill -9 -f "python3 app.py" 2>/dev/null
pkill -9 -f bot_runner 2>/dev/null
pkill -9 -f "bore local" 2>/dev/null
sleep 1

# ۲) شروع پنل
echo "📡 راه‌اندازی پنل..."
nohup python3 app.py > panel.log 2>&1 &
sleep 3

# ۳) شروع ربات
echo "🤖 راه‌اندازی ربات..."
nohup python3 -u bot_runner.py > bot.log 2>&1 &
sleep 2

# ۴) شروع bore.pub برای دسترسی عمومی
echo "🌐 راه‌اندازی bore.pub..."
nohup bore local 8080 --to bore.pub > bore.log 2>&1 &
sleep 5

# ۵) پیدا کردن پورت bore
echo ""
echo "=================== نتایج ==================="
BORE_LINE=$(grep -oP "remote.*?:\K[0-9]+" bore.log | head -1)
if [ -z "$BORE_LINE" ]; then
    BORE_LINE=$(grep -oP "listening at bore.pub:\K[0-9]+" bore.log | head -1)
fi

if [ -n "$BORE_LINE" ]; then
    PUBLIC_URL="http://bore.pub:$BORE_LINE"
    echo "$PUBLIC_URL" > ~/otp_panel/public_url.txt
    echo "✅ آدرس عمومی: $PUBLIC_URL"
    echo "✅ ذخیره شد توی public_url.txt"
else
    echo "⚠️ نتونستم پورت bore رو پیدا کنم"
    echo "📄 لاگ bore:"
    cat bore.log
fi

echo ""
echo "📍 پنل: http://localhost:8080"
echo "📍 پنل ادمین: http://localhost:8080/admin/login"
echo "📍 پنل مشتری: http://localhost:8080/customer"
echo ""
echo "=================== وضعیت ==================="
echo "پنل:"; tail -2 panel.log
echo ""
echo "ربات:"; tail -3 bot.log
echo ""
echo "bore:"; tail -3 bore.log
