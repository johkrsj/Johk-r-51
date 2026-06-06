import os
import re
import logging
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

BOT_TOKEN = os.environ.get("8861550652:AAEPnUDydIOtVRMMQvYcTj-oy09BI04Ci7Y", "")

DOWNLOAD_DIR = "/tmp"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_url(text):
    match = re.search(r"https?://[^\s]+", text)
    return match.group(0) if match else None


def is_supported(url):
    return bool(re.search(r"(tiktok\.com|vm\.tiktok\.com|instagram\.com|instagr\.am)", url))


def download_video(url):
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
            return filepath if os.path.exists(filepath) else None
    except Exception as e:
        logger.error(f"Download error: {e}")
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
        "1️⃣ انسخ رابط الفيديو\n"
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

    if not is_supported(url):
        await update.message.reply_text("❌ الرابط غير مدعوم\nأرسل روابط TikTok أو Instagram فقط")
        return

    platform = "TikTok 🎵" if "tiktok" in url else "Instagram 📸"
    msg = await update.message.reply_text(f"⏳ جاري التحميل من {platform}...")

    filepath = download_video(url)

    if not filepath:
        await msg.edit_text("❌ فشل التحميل، تأكد أن الفيديو عام وحاول مجدداً")
        return

    try:
        if os.path.getsize(filepath) > 50 * 1024 * 1024:
            await msg.edit_text("❌ الفيديو أكبر من 50MB")
            return

        await msg.edit_text("📤 جاري الإرسال...")
        with open(filepath, "rb") as f:
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
        if filepath and os.path.exists(filepath):
            os.remove(filepath)


def main():
    request = HTTPXRequest(
        read_timeout=300,
        write_timeout=300,
        connect_timeout=60,
    )
    app = Application.builder().token(BOT_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ البوت يعمل الآن بـ Polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
