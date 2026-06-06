import os
import re
import logging
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


async def help
