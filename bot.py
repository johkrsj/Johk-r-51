import os
import re
import logging
import requests
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DOWNLOAD_DIR = "/tmp"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_url(text):
    match = re.search(r"https?://[^\s]+", text)
    return match.group(0) if match else None


def is_tiktok(url):
    return bool(re.search(r"(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)", url))


def is_instagram(url):
    return bool(re.search(r"(instagram\.com|instagr\.am)", url))


def download_tiktok(url):
    try:
        api = f"https://tikwm.com/api/?url={url}&hd=1"
        r = requests.get(api, timeout=30)
        data = r.json()
        if data.get("code") == 0:
            item = data["data"]

            # كاروسيل صور
            if item.get("images"):
                files = []
                for i, img_url in enumerate(item["images"]):
                    img_data = requests.get(img_url, timeout=60)
                    filepath = f"{DOWNLOAD_DIR}/tiktok_img_{i}_{os.urandom(4).hex()}.jpg"
                    with open(filepath, "wb") as f:
                        f.write(img_data.content)
                    files.append(("image", filepath))
                return files

            # فيديو عادي
            video_url = item.get("hdplay") or item.get("play")
            if video_url:
                video_data = requests.get(video_url, timeout=60)
                filepath = f"{DOWNLOAD_DIR}/tiktok_{os.urandom(4).hex()}.mp4"
                with open(filepath, "wb") as f:
                    f.write(video_data.content)
                return [("video", filepath)]

    except Exception as e:
        logger.error(f"TikTok download error: {e}")
    return None


def download_instagram(url):
    ydl_opts = {
        "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
        "format": "best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 60,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            if not os.path.exists(filepath):
                filepath = filepath.rsplit(".", 1)[0] + ".mp4"
            if os.path.exists(filepath):
                return [("video", filepath)]
    except Exception as e:
        logger.error(f"Instagram download error: {e}")
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *أهلاً بك في بوت التحميل!*\n\n"
        "📥 أرسل لي رابط من:\n"
        "• TikTok 🎵\n"
        "• Instagram 📸\n\n"
        "وسأحمّل لك الفيديو بأعلى جودة 🚀",
        parse_mode="Markdown"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *طريقة الاستخدام:*\n\n"
        "1 انسخ رابط الفيديو\n"
        "2️⃣ أرسله هنا\n"
        "3️⃣ انتظر ثوانٍ وسيصلك الفيديو ✅\n\n"
        "⚠️ *ملاحظات:*\n"
        "• الفيديو لازم يكون عام\n"
        "• الحد الأقصى 50MB",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = extract_url(update.message.text)

    if not url:
        await update.message.reply_text("❌ ما وجدت رابط، أرسل رابط TikTok أو Instagram")
        return

    if not is_tiktok(url) and not is_instagram(url):
        await update.message.reply_text("❌ الرابط غير مدعوم\nأرسل روابط TikTok أو Instagram فقط")
        return

    platform = "TikTok 🎵" if is_tiktok(url) else "Instagram 📸"
    msg = await update.message.reply_text(f"⏳ جاري التحميل من {platform}...")

    if is_tiktok(url):
        files = download_tiktok(url)
    else:
        files = download_instagram(url)

    if not files:
        await msg.edit_text("❌ فشل التحميل، تأكد أن الفيديو عام وحاول مجدداً")
        return

    try:
        await msg.edit_text("📤 جاري الإرسال...")

        for ftype, filepath in files:
            if os.path.getsize(filepath) > 50 * 1024 * 1024:
                continue
            with open(filepath, "rb") as f:
                if ftype == "image":
                    await update.message.reply_photo(photo=f)
                else:
                    await update.message.reply_video(
                        video=f,
                        caption=f"✅ {platform}",
                        supports_streaming=True,
                        read_timeout=300,
                        write_timeout=300,
                        connect_timeout=60,
                    )

        await msg.delete()

    except Exception as e:
        logger.error(f"Send error: {e}")
        await msg.edit_text("❌ حدث خطأ أثناء الإرسال")
    finally:
        for _, filepath in files:
            if os.path.exists(filepath):
                os.remove(filepath)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("✅ البوت يعمل الآن بـ Polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
