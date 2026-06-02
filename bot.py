import asyncio
import logging
import sqlite3
import uuid
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ================= Configuration =================
BOT_TOKEN = "your_bot_token"
ADMIN_ID = 123456789  # آیدی عددی تلگرام ادمین را اینجا قرار دهید
PRICE_PER_GB = 15000  # قیمت هر گیگابایت به تومان

# ================= Panel Configuration (Marzban) =================
PANEL_URL = "https://sub.your-domain.com"  # آدرس پنل مرزبان شما (بدون اسلش در انتهای آن)
PANEL_USERNAME = "your_admin_username"     # نام کاربری ادمین پنل
PANEL_PASSWORD = "your_admin_password"     # رمز عبور ادمین پنل

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= Database Setup =================
def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Users 
                      (user_id INTEGER PRIMARY KEY, wallet_balance INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT wallet_balance FROM Users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def update_user_balance(user_id, amount):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Users (user_id, wallet_balance) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET wallet_balance = wallet_balance + ?", (user_id, amount, amount))
    conn.commit()
    conn.close()

# ================= API Connection (Panel) =================
async def get_panel_token() -> str:
    """دریافت توکن احراز هویت (Access Token) از پنل مرزبان"""
    async with aiohttp.ClientSession() as session:
        data = {"username": PANEL_USERNAME, "password": PANEL_PASSWORD}
        async with session.post(f"{PANEL_URL}/api/admin/token", data=data) as resp:
            if resp.status == 200:
                json_resp = await resp.json()
                return json_resp.get("access_token")
            else:
                error_msg = await resp.text()
                logging.error(f"Login Error: {error_msg}")
                raise Exception(f"خطا در ورود به پنل. کد وضعیت: {resp.status}")

async def create_vpn_config(user_id: int, gb_amount: int) -> str:
    """
    اتصال واقعی به پنل مرزبان برای ساخت کاربر جدید و دریافت لینک کانفیگ/سابسکریپشن
    """
    try:
        # ۱. دریافت توکن
        token = await get_panel_token()
        
        # ۲. آماده‌سازی اطلاعات کاربر جدید
        bytes_limit = gb_amount * 1073741824  # تبدیل گیگابایت به بایت
        username = f"user_{user_id}_{uuid.uuid4().hex[:4]}"  
        
        payload = {
            "username": username,
            "data_limit": bytes_limit,
            "expire": 0,  
            "proxies": {"vless": {}, "vmess": {}},  
            "note": f"Telegram ID: {user_id}" 
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        # ۳. ارسال درخواست ساخت کاربر به پنل
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{PANEL_URL}/api/user", json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    sub_url = data.get("subscription_url", "")
                    if sub_url:
                        return f"{PANEL_URL}{sub_url}"
                    
                    links = data.get("links", [])
                    if links:
                        return "\n\n".join(links)
                        
                    return "کاربر ساخته شد اما لینکی دریافت نشد. لطفا تنظیمات پنل را بررسی کنید."
                    
                elif resp.status == 409:
                    raise Exception("این نام کاربری از قبل در پنل وجود دارد.")
                else:
                    error_text = await resp.text()
                    logging.error(f"Create User Error: {error_text}")
                    raise Exception(f"خطا در ساخت کاربر. کد: {resp.status}")
                    
    except Exception as e:
        logging.error(f"API Error in create_vpn_config: {str(e)}")
        raise e

# ================= FSM States =================
class BuyVPN(StatesGroup):
    waiting_for_gb = State()

class ChargeWallet(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()

class Support(StatesGroup):
    waiting_for_message = State()

# ================= Keyboards =================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 خرید کانفیگ"), KeyboardButton(text="💳 شارژ حساب")],
        [KeyboardButton(text="👤 حساب کاربری"), KeyboardButton(text="پشتیبانی 🎧")]
    ],
    resize_keyboard=True
)

# ================= Handlers: Start & Profile =================
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    update_user_balance(message.from_user.id, 0)
    await message.answer("سلام! به ربات فروشگاه VPN ما خوش آمدید. 🌸\nلطفاً از منوی زیر انتخاب کنید:", reply_markup=main_menu)

@dp.message(F.text == "👤 حساب کاربری")
async def show_profile(message: Message):
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"👤 شناسه کاربری شما: `{message.from_user.id}`\n💰 موجودی کیف پول: {balance} تومان", parse_mode="Markdown")

# ================= Handlers: Buy VPN =================
@dp.message(F.text == "🛒 خرید کانفیگ")
async def buy_vpn_start(message: Message, state: FSMContext):
    await message.answer(f"لطفاً مقدار حجم مورد نیاز خود را به گیگابایت (فقط عدد) وارد کنید.\n(هر گیگابایت = {PRICE_PER_GB} تومان)")
    await state.set_state(BuyVPN.waiting_for_gb)

@dp.message(BuyVPN.waiting_for_gb)
async def process_buy_vpn(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("لطفاً فقط یک عدد صحیح وارد کنید!")
        return
    
    gb_amount = int(message.text)
    total_price = gb_amount * PRICE_PER_GB
    user_balance = get_user_balance(message.from_user.id)
    
    if user_balance >= total_price:
        # کسر هزینه
        update_user_balance(message.from_user.id, -total_price)
        loading_msg = await message.answer("✅ پرداخت انجام شد. در حال ساخت کانفیگ اختصاصی شما، لطفاً چند لحظه صبر کنید... ⏳")
        
        try:
            # ساخت کانفیگ مستقیم از پنل
            new_config = await create_vpn_config(message.from_user.id, gb_amount)
            await loading_msg.delete()
            await message.answer(f"🎉 کانفیگ شما با موفقیت ساخته شد!\n\nحجم: {gb_amount} گیگابایت\nمبلغ کسر شده: {total_price} تومان\n\nلینک سابسکریپشن/کانفیگ شما:\n`{new_config}`", parse_mode="Markdown")
        except Exception as e:
            # برگشت پول در صورت بروز خطای سرور
            update_user_balance(message.from_user.id, total_price)
            await loading_msg.delete()
            await message.answer("❌ متأسفانه در ارتباط با سرور مشکلی پیش آمد. مبلغ به کیف پول شما برگشت داده شد. لطفاً به پشتیبانی اطلاع دهید.")
        
        await state.clear()
    else:
        # هدایت هوشمند به بخش شارژ حساب و ذخیره حجم درخواستی
        await state.update_data(amount=total_price, gb_amount=gb_amount)
        await message.answer(f"❌ موجودی شما کافی نیست.\nمبلغ مورد نیاز: {total_price} تومان\n\nلطفاً این مبلغ را به شماره کارت `1234-5678-1234-5678` واریز کرده و عکس رسید خود را همینجا ارسال کنید تا حساب شما شارژ شود.", parse_mode="Markdown")
        await state.set_state(ChargeWallet.waiting_for_receipt)

# ================= Handlers: Charge Wallet =================
@dp.message(F.text == "💳 شارژ حساب")
async def charge_wallet_start(message: Message, state: FSMContext):
    await message.answer("لطفاً مبلغی که قصد شارژ دارید را به تومان (فقط عدد) وارد کنید:")
    await state.set_state(ChargeWallet.waiting_for_amount)

@dp.message(ChargeWallet.waiting_for_amount)
async def process_charge_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("لطفاً فقط عدد وارد کنید!")
        return
    
    await state.update_data(amount=int(message.text), gb_amount="شارژ دلخواه کیف پول")
    await message.answer("لطفاً مبلغ را به شماره کارت `1234-5678-1234-5678` واریز کرده و عکس رسید خود را همینجا ارسال کنید.", parse_mode="Markdown")
    await state.set_state(ChargeWallet.waiting_for_receipt)

@dp.message(ChargeWallet.waiting_for_receipt, F.photo)
async def process_charge_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get('amount')
    gb_amount = data.get('gb_amount', 'نامشخص')
    
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "ندارد"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تایید و شارژ", callback_data=f"approve_{user_id}_{amount}"),
         InlineKeyboardButton(text="❌ رد کردن", callback_data=f"reject_{user_id}")]
    ])
    
    # ساخت کپشن کامل برای ادمین
    caption_text = (
        f"🧾 **درخواست بررسی رسید پرداخت**\n\n"
        f"👤 شناسه عددی: `{user_id}`\n"
        f"💬 یوزرنیم: {username}\n"
        f"💰 مبلغ واریزی: {amount} تومان\n"
        f"📦 حجم درخواستی: {gb_amount} گیگابایت\n"
        f"🕒 تاریخ و ساعت: {current_time}"
    )
    
    await bot.send_photo(
        chat_id=ADMIN_ID, 
        photo=message.photo[-1].file_id, 
        caption=caption_text,
        reply_markup=admin_kb,
        parse_mode="Markdown"
    )
    
    await message.answer("✅ رسید شما با موفقیت برای مدیریت ارسال شد. پس از تایید، حساب شما شارژ خواهد شد و می‌توانید خرید خود را انجام دهید.")
    await state.clear()

# ================= Admin Callbacks =================
@dp.callback_query(F.data.startswith("approve_"))
async def approve_charge(callback: CallbackQuery):
    _, user_id, amount = callback.data.split("_")
    update_user_balance(int(user_id), int(amount))
    
    await bot.send_message(chat_id=int(user_id), text=f"🎉 حساب شما با موفقیت به مبلغ {amount} تومان شارژ شد. هم اکنون می‌توانید از منوی '🛒 خرید کانفیگ' سرویس خود را دریافت کنید.")
    
    # آپدیت پیام ادمین تا دکمه‌ها حذف شوند و وضعیت تغییر کند
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ وضعیت: **تایید و شارژ شد.**", parse_mode="Markdown")
    await callback.answer("حساب کاربر شارژ شد.")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_charge(callback: CallbackQuery):
    _, user_id = callback.data.split("_")
    
    await bot.send_message(chat_id=int(user_id), text="❌ درخواست شارژ شما توسط مدیریت رد شد. در صورت بروز مشکل با پشتیبانی در تماس باشید.")
    
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ وضعیت: **رد شد.**", parse_mode="Markdown")
    await callback.answer("رسید رد شد.")

# ================= Handlers: Support & Tickets =================
@dp.message(F.text == "پشتیبانی 🎧")
async def support_start(message: Message, state: FSMContext):
    await message.answer("لطفاً پیام خود را بنویسید تا برای پشتیبانی ارسال شود:")
    await state.set_state(Support.waiting_for_message)

@dp.message(Support.waiting_for_message)
async def process_support_message(message: Message, state: FSMContext):
    await bot.send_message(chat_id=ADMIN_ID, text=f"📩 پیام جدید از کاربر: `{message.from_user.id}`", parse_mode="Markdown")
    await message.forward(chat_id=ADMIN_ID)
    await message.answer("پیام شما برای پشتیبانی ارسال شد. منتظر پاسخ باشید. 🌸")
    await state.clear()

@dp.message(F.reply_to_message & (F.from_user.id == ADMIN_ID))
async def admin_reply_to_user(message: Message):
    if message.reply_to_message.forward_from:
        user_id = message.reply_to_message.forward_from.id
        await bot.send_message(chat_id=user_id, text=f"👨‍💻 پاسخ پشتیبانی:\n\n{message.text}")
    else:
        await message.answer("کاربر شناسه خود را مخفی کرده است، امکان ارسال مستقیم پاسخ وجود ندارد.")

# ================= Main =================
async def main():
    init_db()
    print("Bot is starting with Direct Panel API feature...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())