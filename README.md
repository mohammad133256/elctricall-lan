# Electrical Industrial Lab

نرم‌افزار آموزشی و محاسباتی برق صنعتی (نسخه MVP)

## محتویات پروژه

- `main.py` → کد اصلی برنامه
- `fonts/` → فونت فارسی (Cairo)
- `buildozer.spec` → تنظیمات ساخت APK
- `requirements.txt` → وابستگی‌ها

---

## اجرا روی کامپیوتر (تست)

```bash
pip install kivy==2.3.1 kivymd==1.2.0
python main.py
```

---

## ساخت APK (Android)

### پیش‌نیازها (روی سیستم لینوکس):

```bash
sudo apt update
sudo apt install -y git unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
pip install buildozer cython
```

### مراحل ساخت:

1. وارد پوشه پروژه شو:
```bash
cd ElectricalIndustrialLab
```

2. اولین بار این دستور را بزن (دانلود SDK و NDK طول می‌کشد):
```bash
buildozer android debug
```

3. بعد از تمام شدن، فایل APK اینجا ساخته می‌شود:
```
bin/electricallab-1.0.0-arm64-v8a-debug.apk
```

### نکات مهم:

- اولین ساخت ممکن است ۴۵ دقیقه تا ۲ ساعت طول بکشد.
- نیاز به اینترنت پایدار و حدود ۸–۱۲ گیگ فضای خالی دارد.
- اگر خطا داد، معمولاً با زدن دوباره `buildozer android debug` حل می‌شود.

---

## ساخت APK با Google Colab (ساده‌تر)

می‌توانی از نوت‌بوک‌های آماده Buildozer در Google Colab هم استفاده کنی.  
فقط پوشه پروژه را آپلود کن و دستور `buildozer android debug` را اجرا کن.

---

## هشدار

این برنامه جنبه آموزشی دارد.  
نتایج محاسبات کابل و موتور باید با استانداردها و دیتاشیت سازنده تأیید شوند.
