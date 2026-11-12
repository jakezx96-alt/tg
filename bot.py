import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
import yt_dlp

# --- НАСТРОЙКИ БОТА ---
TOKEN = "8936358808:AAE__GPtgV-2UpuXYE-cTm8gv73Dzh5elzA"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ЛОГИКА ПОИСКА И СКЧИВАНИЯ МУЗЫКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Отправь мне ссылку на трек или название песни/исполнителя, и я найду и скачаю для тебя аудио!"
    )

@dp.message(F.text)
async def search_music(message: types.Message):
    query = message.text.strip()
    if not query:
        return

    status_msg = await message.answer("🔍 Ищу и скачиваю трек...")

    # Определяем, ссылка это или поисковый запрос
    if query.startswith("http://") or query.startswith("https://"):
        search_target = query
    else:
        search_target = f"ytsearch1:{query}"

    # Настройки yt-dlp с подключением файла кук для обхода блокировок
    ydl_opts = {
        'format': 'bestaudio/best',
        'cookiefile': 'cookies.txt',  # Авторизация через ваш файл кук
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
    }

    try:
        os.makedirs("downloads", exist_ok=True)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_target, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            filename = ydl.prepare_filename(info)
            audio_file = os.path.splitext(filename)[0] + ".mp3"

        # Отправляем готовый MP3 файл пользователю
        audio = types.FSInputFile(audio_file)
        await message.answer_audio(audio=audio, title=info.get('title', 'Audio'))
        
        # Удаляем временный файл с сервера
        if os.path.exists(audio_file):
            os.remove(audio_file)
            
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"⚠️ Ошибка при скачивании: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
