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

# إعداد السجلات (Logs)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ELEVENLABS_API_KEY = "sk_db6ede198600473c15c25defbd5d97d9a777"

# أصوات ElevenLabs المحددة (يمكنك تغيير الـ Voice ID لاحقاً)
ELEVEN_VOICES = {
    "sa_f": "21m00Tcm4TlvDq8ikWAM",  # Rachel (صوت مجاني أساسي ومضمون)
    "sa_m": "ErXwobaYiN019PkySvjV",  # Antoni
}
# قائمة الأصوات الكاملة لـ Edge-TTS والدعم الاحتياطي
VOICES = {
    "sa_f": {"name": "🇸🇦 سعودي (أنثى - زارية)", "voice": "ar-SA-ZariyahNeural"},
    "sa_m": {"name": "🇸🇦 سعودي (ذكر - حامد)", "voice": "ar-SA-HamedNeural"},
    "eg_f": {"name": "🇪🇬 مصري (أنثى - سلمى)", "voice": "ar-EG-SalmaNeural"},
    "eg_m": {"name": "🇪🇬 مصري (ذكر - شاكر)", "voice": "ar-EG-ShakirNeural"},
    "ae_f": {"name": "🇦🇪 إماراتي (أنثى - فاطمة)", "voice": "ar-AE-FatimaNeural"},
    "ae_m": {"name": "🇦🇪 إماراتي (ذكر - حمدان)", "voice": "ar-AE-HamdanNeural"},
    "sy_f": {"name": "🇸🇾 سوري (أنثى - أمل)", "voice": "ar-SY-AmanyNeural"},
    "iq_m": {"name": "🇮🇶 عراقي (ذكر - باسل)", "voice": "ar-IQ-BasselNeural"},
}

def get_voices_keyboard():
    keyboard = []
    keys = list(VOICES.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(VOICES[keys[i]]["name"], callback_data=f"set_{keys[i]}")]
        if i + 1 < len(keys):
            row.append(InlineKeyboardButton(VOICES[keys[i+1]]["name"], callback_data=f"set_{keys[i+1]}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

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
    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True
        else:
    logging.warning(f"ElevenLabs Error: {response.status_code} - {response.text}")
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "selected_voice" not in context.user_data:
        context.user_data["selected_voice"] = "sa_f"
        
    current_voice_name = VOICES[context.user_data["selected_voice"]]["name"]
    
    msg = (
        "👋 **أهلاً بك في بوت تحويل النص إلى صوت!**\n\n"
        f"🎙️ **الصوت المختار حالياً:** {current_voice_name}\n\n"
        "✨ **طريقة الاستخدام:**\n"
        "أرسل أي نص في الشات وسأقوم بتحويله إلى مقطع صوتي مباشرة.\n\n"
        "⚙️ **لتغيير الصوت أو اللهجة:** أرسل الأمر /voices"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def voices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_key = context.user_data.get("selected_voice", "sa_f")
    current_voice_name = VOICES[current_key]["name"]
    
    await update.message.reply_text(
        f"🎙️ **اختر الصوت أو اللهجة المفضلة لديك:**\n(الصوت الحالي: {current_voice_name})",
        reply_markup=get_voices_keyboard(),
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("set_"):
        voice_key = data.replace("set_", "")
        if voice_key in VOICES:
            context.user_data["selected_voice"] = voice_key
            selected_name = VOICES[voice_key]["name"]
            
            await query.edit_message_text(
                f"✅ **تم تغيير الصوت بنجاح إلى:**\n{selected_name}\n\n"
                "الان أرسل أي نص وسأقوم بتحويله بصوت الشخصية المختارة!",
                parse_mode="Markdown"
            )

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
        
        # المحاولة الثانية (احتياطية): استخدام Edge-TTS في حال نفاد الحروف أو عدم توفر API Key
        if not success:
            edge_voice_name = VOICES.get(voice_key, {}).get("voice", "ar-SA-ZariyahNeural")
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

if __name__ == "__main__":
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing!")
        
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("voices", voices_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)
