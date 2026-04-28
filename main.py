import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ===== ENV LOAD =====
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

# ===== LOGGING =====
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== STATE =====
class Form(StatesGroup):
    complaint = State()
    suggestion = State()

# ===== KEYBOARDS =====
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📩 Shikoyat")],
        [KeyboardButton(text="💡 Taklif")],
        [KeyboardButton(text="❌ Tugatish")]
    ],
    resize_keyboard=True
)

send_btn = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📤 Yuborish")],
        [KeyboardButton(text="❌ Bekor qilish")]
    ],
    resize_keyboard=True
)

# ===== ERROR HANDLER =====
@dp.errors()
async def global_error_handler(event, exception):
    logging.exception(f"Xatolik: {exception}")
    return True

# ===== START =====
@dp.message(CommandStart())
async def start_handler(msg: Message):
    await msg.answer("Bo‘limni tanlang:", reply_markup=menu)

# ===== BOSHLASH =====
@dp.message(F.text == "📩 Shikoyat")
async def complaint_start(msg: Message, state: FSMContext):
    await state.set_state(Form.complaint)
    await state.update_data(messages=[], type="complaint")
    await msg.answer("Shikoyatingizni yuboring:(rasm,matn,video,ovozli habar)", reply_markup=send_btn)

@dp.message(F.text == "💡 Taklif")
async def suggestion_start(msg: Message, state: FSMContext):
    await state.set_state(Form.suggestion)
    await state.update_data(messages=[], type="suggestion")
    await msg.answer("Taklifingizni yuboring:(rasm,matn,video,ovozli habar)", reply_markup=send_btn)

# ===== YUBORISH =====
@dp.message(F.text == "📤 Yuborish")
async def send_all(msg: Message, state: FSMContext):
    try:
        data = await state.get_data()
        messages = data.get("messages", [])
        msg_type = data.get("type")

        if not messages:
            await msg.answer("❗ Hech narsa yuborilmadi")
            return

        title = {
            "complaint": "📩 Yangi shikoyat",
            "suggestion": "💡 Yangi taklif"
        }.get(msg_type, "📨 Yangi murojaat")

        user = msg.from_user

        for admin in ADMIN_IDS:
            await bot.send_message(
                admin,
                f"{title}\nUser ID: {user.id}"
            )

            for m_id in messages:
                try:
                    await bot.copy_message(
                        chat_id=admin,
                        from_chat_id=msg.chat.id,
                        message_id=m_id
                    )
                except Exception as e:
                    logging.warning(f"Copy xato: {e}")

        await state.clear()

        await msg.answer(
            "✅ Hammasi yuborildi!\n\nYangi murojaat uchun menyudan foydalaning 👇",
            reply_markup=menu
        )

    except Exception as e:
        logging.exception(e)
        await msg.answer("❌ Xatolik yuz berdi")

# ===== BEKOR =====
@dp.message(F.text == "❌ Bekor qilish")
async def cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Bekor qilindi", reply_markup=menu)

# ===== TUGATISH =====
@dp.message(F.text == "❌ Tugatish")
async def finish(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "❗ Jarayon tugatildi.\nQayta boshlash uchun /start buyrug‘ini bosing.",
        reply_markup=ReplyKeyboardRemove()
    )

# ===== YIG‘ISH =====
@dp.message(Form.complaint, ~F.text.in_(["📤 Yuborish", "❌ Bekor qilish"]))
async def collect_complaint(msg: Message, state: FSMContext):
    data = await state.get_data()
    messages = data.get("messages", [])

    messages.append(msg.message_id)
    await state.update_data(messages=messages)

    await msg.answer(f"➕ Qo‘shildi ({len(messages)} ta)")

@dp.message(Form.suggestion, ~F.text.in_(["📤 Yuborish", "❌ Bekor qilish"]))
async def collect_suggestion(msg: Message, state: FSMContext):
    data = await state.get_data()
    messages = data.get("messages", [])

    messages.append(msg.message_id)
    await state.update_data(messages=messages)

    await msg.answer(f"➕ Qo‘shildi ({len(messages)} ta)")

# ===== RUN =====
async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())