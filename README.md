# 🚀 MinimalVPN-Bot

> "The art of engineering is in what you *don't* build." 
> «هنر مهندسی، در نساختنِ زوائد است.»

**MinimalVPN-Bot** is an ultra-lightweight, MVP-focused Telegram Bot for selling VPN configurations. Designed with simplicity in mind, it skips heavy databases and complex panels, focusing purely on the core business flow: **Wallet Recharge, Buying Configs, and Customer Support.**

این پروژه یک ربات تلگرامی فوق‌العاده سبک و مینیمال برای فروش کانفیگ‌های VPN است. این ربات با تمرکز بر اصل MVP (کمینه محصول پذیرفتنی)، از دیتابیس‌های سنگین و پیچیدگی‌های غیرضروری دوری کرده و فقط روی هسته اصلی کار تمرکز دارد: **شارژ کیف پول، خرید کانفیگ و پشتیبانی.**

---

## ✨ Features | ویژگی‌ها

- 🛒 **Simple Purchasing Flow:** Users input desired GBs, cost is calculated ($$Total\_Cost = Volume \times Price$$), and deducted from the wallet.
- 💳 **Wallet & Receipt System:** Manual wallet top-up via sending payment receipts to the admin for approval.
- 🎧 **Built-in Support:** Forward-based ticketing system allowing admins to reply to users directly from the bot.
- 🗄️ **Zero-Config Database:** Uses standard `sqlite3` stored right next to your code. No Docker or heavy SQL servers needed.
- ⚡ **Modern Stack:** Built with `Python 3` and `aiogram 3.x`.

---

## 🛠️ Tech Stack | ابزارهای استفاده شده

- **Language:** Python 3.9+
- **Framework:** [aiogram 3.x](https://docs.aiogram.dev/en/latest/) (Asynchronous Telegram Bot API)
- **Database:** SQLite (Built-in)
- **Architecture:** FSM (Finite State Machine) for handling user flows.

---

## ⚙️ Installation & Setup | نصب و راه‌اندازی

### 1. Clone the repository
ابتدا پروژه را کلون کنید:
```bash
git clone https://github.com/YourUsername/MinimalVPN-Bot.git
cd MinimalVPN-Bot

### 2. Install dependencies
کتابخانه‌های مورد نیاز را نصب کنید:
bash
pip install aiogram

### 3. Configuration
فایل `bot.py` را باز کرده و متغیرهای زیر را در ابتدای کد با اطلاعات خود جایگزین کنید:
python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # توکن ربات شما از BotFather
ADMIN_ID = 123456789             # آیدی عددی تلگرام ادمین (برای دریافت رسیدها و پیام‌ها)
PRICE_PER_GB = 5000              # قیمت هر گیگابایت به تومان

### 4. Run the bot
ربات را اجرا کنید. دیتابیس `shop.db` به صورت خودکار در اولین اجرا ساخته می‌شود:
bash
python bot.py

---

## 🗂️ Database Structure | ساختار دیتابیس

The bot automatically creates a `shop.db` file with two simple tables:
دیتابیس دارای دو جدول بسیار ساده است:

1. **`Users` Table:**
   - `user_id` (Primary Key)
   - `wallet_balance` (Integer, Default: 0)

2. **`Configs` Table:**
   - `id` (Primary Key, AutoIncrement)
   - `config_string` (Text - The actual VPN config data)
   - `is_sold` (Boolean/Integer, Default: 0)

*Note: You can manually insert your generated configs into the `Configs` table using any SQLite viewer (like DB Browser for SQLite).*
*نکته: شما می‌توانید کانفیگ‌های تولید شده خود را با استفاده از نرم‌افزارهایی مثل DB Browser for SQLite به صورت دستی وارد جدول `Configs` کنید.*

---

## 🤝 Contributing | مشارکت

Contributions, issues, and feature requests are welcome! Keep in mind the philosophy of this project: **Keep it minimal.** 
از مشارکت شما استقبال می‌شود! فقط لطفاً فلسفه پروژه را در نظر داشته باشید: **حفظ سادگی و مینیمال بودن.**

## 📜 License
This project is licensed under the MIT License.


### چند پیشنهاد دوستانه برای گیت‌هاب:
*   یادت باشه نام کاربری گیت‌هابت رو در بخش Clone (جای `YourUsername`) جایگزین کنی.
*   اگر دوست داشتی، می‌تونی یک اسکرین‌شات از محیط ربات (مثلاً همون دکمه‌های شیشه‌ای تایید و رد شارژ) بگیری و به پوشه پروژه اضافه کنی و عکسش رو تو README بذاری؛ این کار جذابیت بصری ریپازیتوری رو صدچندان می‌کنه!

امیدوارم این ریپازیتوری به یک نمونه کار درخشان در رزومه‌ات تبدیل بشه. اگر نیاز به ویرایش یا اضافه کردن بخش خاصی به این README داری، با کمال میل در خدمتم! 🌟
