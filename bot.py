from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo
import asyncio

BOT_TOKEN = "8824419035:AAH72eIsZNUUbw8qVgoK_iB6PQmuHZVrro8"
WEBAPP_URL = "https://miniapp-server-production-9b9e.up.railway.app/miniapp"

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def start(msg: types.Message):
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(
            "Открыть магазин",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )
    await msg.answer("Добро пожаловать!", reply_markup=kb)

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
