"""دستورات ادمین برای مدیریت محصولات"""


def parse_add_command(text):
    """پردازش دستور /add برای اضافه کردن محصول
    
    فرمت: /add نام | قیمت | نام‌های دیگر | واحد | توضیح
    
    مثال: /add کرفس | 56000 | celery,کرفس | کیلو | کرفس تازه
    """
    if not text.startswith("/add "):
        return None
    
    parts = text[5:].split("|")
    if len(parts) < 2:
        return None
    
    return {
        "name": parts[0].strip(),
        "price": parts[1].strip(),
        "aliases": parts[2].strip() if len(parts) > 2 else "",
        "unit": parts[3].strip() if len(parts) > 3 else "کیلو",
        "description": parts[4].strip() if len(parts) > 4 else ""
    }


def parse_remove_command(text):
    """پردازش /remove نام محصول"""
    if not text.startswith("/remove "):
        return None
    return text[8:].strip()


def parse_set_command(text):
    """پردازش /set برای تنظیم اطلاعات مغازه
    
    /set shop_name میوه فروشی نایسود
    /set address تهران، خیابان...
    /set phone 09123456789
    /set hours هر روز ۸ تا ۲۲
    """
    if not text.startswith("/set "):
        return None
    
    parts = text[5:].split(None, 1)
    if len(parts) < 2:
        return None
    
    return {"field": parts[0].strip(), "value": parts[1].strip()}
