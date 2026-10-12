from adapters.kavenegar_adapter import send_sms

# ⬇️ شماره‌ی خودت رو اینجا بنویس
my_number = "09916183900"

result = send_sms(my_number, "تست پنل پیامکی ✅")
print("نتیجه:", result)
