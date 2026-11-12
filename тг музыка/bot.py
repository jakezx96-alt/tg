import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
import yt_dlp

# --- НАСТРОЙКИ БОТА ---
# Вставьте сюда токен вашего Telegram-бота
TOKEN = "8936358808:AAE__GPtgV-2UpuXYE-cTm8gv73Dzh5elzA"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# --- ЛОГИКА ПОИСКА И СКАЧИВАНИЯ МУЗЫКИ (yt-dlp на 10 треков) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Отправь мне название песни или имя исполнителя, а я найду для тебя до 10 вариантов."
    )


@dp.message()
async def search_music(message: types.Message):
    query = message.text
    if not query:
        return

    wait_msg = await message.answer("🔍 Ищу треки на YouTube...")

    # Настройки yt-dlp для поиска 10 вариантов
    ydl_opts = {
        "format": "bestaudio/best",
        "default_search": "ytsearch10",
        "noplaylist": True,
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get("entries", [])

        if not entries:
            await wait_msg.edit_text("❌ Ничего не найдено по вашему запросу.")
            return

        # Создаем инлайн-кнопки с результатами поиска
        keyboard_buttons = []
        for i, entry in enumerate(entries[:10], 1):
            title = entry.get("title", "Без названия")
            video_id = entry.get("id")
            # Передаем id трека через callback_data
            keyboard_buttons.append([
                types.InlineKeyboardButton(
                    text=f"{i}. {title[:50]}...",
                    callback_data=f"dl_{video_id}",
                )
            ])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await wait_msg.edit_text(
            "🎵 Вот что удалось найти (выберите трек для скачивания):",
            reply_markup=keyboard,
        )

    except Exception as e:
        await wait_msg.edit_text(f"⚠️ Произошла ошибка при поиске: {e}")


# Обработчик нажатия на кнопку скачивания трека
@dp.callback_query(F.data.startswith("dl_"))
async def download_track(callback: types.CallbackQuery):
    video_id = callback.data.split("_")[1]
    url = f"https://www.youtube.com/watch?v={video_id}"

    await callback.message.edit_text("📥 Скачиваю и конвертирую трек...")

    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_file = os.path.splitext(filename)[0] + ".mp3"

        # Отправляем готовый аудиофайл пользователю
        audio = types.FSInputFile(mp3_file)
        await callback.message.answer_audio(audio=audio)

        # Удаляем файл с диска после отправки
        if os.path.exists(mp3_file):
            os.remove(mp3_file)

        await callback.message.delete()

    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка при скачивании файла: {e}")


# --- ВЕБ-СЕРВЕР ДЛЯ ПРЕДОТВРАЩЕНИЯ СНА НА RENDER ---

async def handle(request):
    return web.Response(text="I am alive!")


async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render передает порт через системную переменную PORT, по умолчанию берем 8080
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# --- ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА ---

async def main():
    # Запускаем фоновый веб-сервер, чтобы бот не засыпал
    asyncio.create_task(web_server())
    # Запускаем самого Telegram-бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())