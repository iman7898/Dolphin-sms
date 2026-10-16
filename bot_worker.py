"""
🤖 Bot Worker — اجراکنندهٔ تسک‌های AI Manager
اجرا: python3 bot_worker.py
"""
import time
import json
import sys
from datetime import datetime
from database import (get_pending_tasks, update_task_status, get_bot_token,
                      get_ai_config, log_bot_action)

# آداپترها
try:
    from bot_adapters.rubika import RubikaBot
    from bot_adapters.telegram import TelegramBot
    from bot_adapters.bale import BaleBot
except Exception as e:
    print(f"⚠️ خطا در ایمپورت آداپترها: {e}")
    sys.exit(1)


def check_force_join(user_id, messenger, chat_id, bot):
    """چک می‌کنه کاربر عضو کانال‌های Force-Join هست یا نه"""
    try:
        from database import get_force_joins
        channels = get_force_joins(user_id, messenger)
        active = [c for c in channels if c[4]]
        if not active:
            return True, []
        # اگه ربات API داره که عضویت رو چک کنه، ازش استفاده کن
        # وگرنه فرض می‌کنیم کاربر باید خودش جوین کنه
        not_joined = [c[3] for c in active]  # لینک‌ها
        return False, not_joined
    except Exception as e:
        return True, []


def get_bot_instance(messenger, token):
    if not token:
        return None
    if messenger == 'rubika':
        return RubikaBot(token)
    elif messenger == 'telegram':
        return TelegramBot(token)
    elif messenger == 'bale':
        return BaleBot(token)
    return None


def run_recruit_task(user_id, payload, messenger, token, channel):
    """عضوآوری — ارسال پیام دعوت + اطلاع‌رسانی"""
    bot = get_bot_instance(messenger, token)
    if not bot:
        return False, "آداپتر پیدا نشد"

    try:
        # چک اتصال
        me = bot.get_me()
        if not me or (me.get('ok') is False and me.get('status') == 'error'):
            return False, f"اتصال ناموفق: {me.get('message', '')}"

        target = payload.get('target_count', 100)
        invite_msg = payload.get('invite_message') or "به کانال ما بپیوندید!"
        invite_link = payload.get('invite_link') or channel

        # ارسال پیام تست
        full_msg = f"{invite_msg}\n\n🔗 {invite_link}"
        chat_id = payload.get('chat_id') or channel
        r = bot.send_message(chat_id, full_msg)

        ok = (r.get('ok') is not False) and (r.get('status') != 'error')
        if ok:
            return True, f"پیام دعوت ارسال شد به {chat_id}"
        else:
            return False, f"خطا در ارسال: {r.get('message') or r.get('description', '')}"
    except Exception as e:
        return False, f"استثنا: {e}"


def run_content_task(user_id, payload, messenger, token, target):
    """محتوا — فوروارد از کانال‌های منبع با فیلتر کلیدواژه"""
    bot = get_bot_instance(messenger, token)
    if not bot:
        return False, "آداپتر پیدا نشد"

    try:
        me = bot.get_me()
        if not me:
            return False, "اتصال ناموفق"

        sources_raw = payload.get('sources', '') or ''
        sources = [s.strip() for s in sources_raw.split(',') if s.strip()]
        keywords = [k.strip() for k in (payload.get('keywords', '') or '').split(',') if k.strip()]
        real_target = payload.get('target') or target

        if not sources:
            return False, "کانال منبعی تعریف نشده"
        if not real_target:
            return False, "کانال مقصد تعریف نشده"

        # پیام تست به کانال مقصد
        test_msg = f"📝 ربات محتوا فعال شد
📥 منابع: {', '.join(sources[:3])}
🎯 مقصد: {real_target}"
        if keywords:
            test_msg += f"
🔍 کلیدواژه: {', '.join(keywords)}"
        r = bot.send_message(real_target, test_msg)
        if r:
            ok = (r.get('ok') is not False) and (r.get('status') != 'error') and (r.get('status') != 'INVALID_ACCESS')
            if ok:
                return True, f"ربات محتوا فعال شد ({len(sources)} کانال منبع)"
            else:
                return False, f"خطا: {r.get('message') or r.get('description') or r.get('dev_message', '')}"
        return False, "بدون پاسخ"
    except Exception as e:
        return False, f"استثنا: {e}"


def process_task(task):
    tid, user_id, task_type, messenger, payload_str, sched = task
    try:
        payload = json.loads(payload_str or '{}')
    except:
        payload = {}

    # گرفتن توکن کاربر
    creds = get_bot_token(user_id)
    if not creds or not creds['token']:
        update_task_status(tid, 'failed', 'توکن ربات تنظیم نشده')
        log_bot_action(user_id, tid, 'skip', 'no token')
        return False, "توکن نیست"

    token = creds['token']
    real_messenger = creds.get('messenger') or messenger or 'rubika'
    channel = creds.get('channel') or ''

    # اجرا بر اساس نوع
    if task_type == 'recruit_start':
        ok, msg = run_recruit_task(user_id, payload, real_messenger, token, channel)
    elif task_type == 'content_start':
        ok, msg = run_content_task(user_id, payload, real_messenger, token, channel)
    else:
        ok, msg = False, f"نوع تسک ناشناخته: {task_type}"

    status = 'done' if ok else 'failed'
    update_task_status(tid, status, msg)
    log_bot_action(user_id, tid, status, msg)
    return ok, msg


def main():
    print("=" * 50)
    print("🤖 Bot Worker Started")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    while True:
        try:
            tasks = get_pending_tasks(5)
            if tasks:
                for t in tasks:
                    print(f"🔧 اجرای تسک #{t[0]} ({t[2]}) برای کاربر {t[1]}")
                    ok, msg = process_task(t)
                    emoji = "✅" if ok else "❌"
                    print(f"   {emoji} {msg}")
            else:
                # هیچ تسکی نیست — استراحت
                pass
        except Exception as e:
            print(f"⚠️ خطا: {e}")

        time.sleep(15)  # هر ۱۵ ثانیه چک کن


if __name__ == "__main__":
    main()
