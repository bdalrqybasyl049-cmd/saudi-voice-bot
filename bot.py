import os
import logging
import asyncio
import requests
import edge_tts
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# أصوات ElevenLabs المحددة (يمكنك إضافة Voice ID الخاص بك)
ELEVEN_VOICES = {
    "sa_f": "21m00Tcm4TlvDq8ikWAM",  # مثال لـ Voice ID
    "sa_m": "ErXwobaYiN019PkySvjV",
}

# أصوات Edge-TTS الاحتياطية
EDGE_VOICES = {
    "sa_f": "ar-SA-ZariyahNeural",
    "sa_m": "ar-SA-HamedNeural",
    "eg_f": "ar-EG-SalmaNeural",
    "eg_m": "ar-EG-ShakirNeural",
}

def generate_elevenlabs_audio(text, voice_id, output_path):
    if not ELEVENLABS_API_KEY:
        return False
        
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    else:
        logging.warning(f"ElevenLabs failed/out of characters. Status: {response.status_code}")
        return False

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("/"):
        return
        
    voice_key = context.user_data.get("selected_voice", "sa_f")
    status_msg = await update.message.reply_text("⏳ جاري توليد المقطع الصوتي بأعلى جودة...")
    output_file = f"voice_{update.message.from_user.id}.mp3"
    
    try:
        # المحاولة الأولى: استخدام ElevenLabs
        eleven_voice_id = ELEVEN_VOICES.get(voice_key, "21m00Tcm4TlvDq8ikWAM")
        success = generate_elevenlabs_audio(text, eleven_voice_id, output_file)
        
        # المحاولة الثانية (احتياطية): استخدام Edge-TTS في حال نفاد الحروف أو حدوث خطأ
        if not success:
            edge_voice_name = EDGE_VOICES.get(voice_key, "ar-SA-ZariyahNeural")
            communicate = edge_tts.Communicate(text, edge_voice_name, rate="+5%")
            await communicate.save(output_file)
        
        with open(output_file, "rb") as audio:
            await update.message.reply_voice(voice=audio, caption=f"🗣️ النص: {text[:50]}...")
            
        await status_msg.delete()
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text("❌ حدث خطأ أثناء تحويل النص إلى صوت.")
        
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)
