import os
import logging
import asyncio
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

# قائمة الأصوات المتاحة (عربية وعالمية)
VOICES = {
    # الأصوات العربية
    "sa_f": {"name": "🇸🇦 سعودي (أنثى - زارية)", "voice": "ar-SA-ZariyahNeural"},
    "sa_m": {"name": "🇸🇦 سعودي (ذكر - حامد)", "voice": "ar-SA-HamedNeural"},
    "eg_f": {"name": "🇪🇬 مصري (أنثى - سلمى)", "voice": "ar-EG-SalmaNeural"},
    "eg_m": {"name": "🇪🇬 مصري (ذكر - شاكر)", "voice": "ar-EG-ShakirNeural"},
    "ae_f": {"name": "🇦🇪 إماراتي (أنثى - فاطمة)", "voice": "ar-AE-FatimaNeural"},
    "ae_m": {"name": "🇦🇪 إماراتي (ذكر - حمدان)", "voice": "ar-AE-HamdanNeural"},
    "ye_m": {"name": "🇾🇪 يمني (ذكر - مريم/علي)", "voice": "ar-YE-MaryamNeural"},
    "sy_f": {"name": "🇸🇾 سوري (أنثى - أمل)", "voice": "ar-SY-AmanyNeural"},
    "iq_m": {"name": "🇮🇶 عراقي (ذكر - باسل)", "voice": "ar-IQ-BasselNeural"},
    
    # أصوات عالمية مميزة
    "us_f": {"name": "🇺🇸 إنجليزي أمريكي (أنثى - Ava)", "voice": "en-US-AvaNeural"},
    "us_m": {"name": "🇺🇸 إنجليزي أمريكي (ذكر - Guy)", "voice": "en-US-GuyNeural"},
    "fr_f": {"name": "🇫🇷 فرنسي (أنثى - Denise)", "voice": "fr-FR-DeniseNeural"},
    "tr_f": {"name": "🇹🇷 تركي (أنثى - Emel)", "voice": "tr-TR-EmelNeural"},
}

def get_voices_keyboard():
    keyboard = []
    keys = list(VOICES.keys())
    # تنظيم الأزرار في صفين لكل سطر
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(VOICES[keys[i]]["name"], callback_data=f"set_{keys[i]}")]
        if i + 1 < len(keys):
            row.append(InlineKeyboardButton(VOICES[keys[i+1]]["name"], callback_data=f"set_{keys[i+1]}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # تعيين الصوت الافتراضي (سعودي أنثى) إذا لم يكن محددًا
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
    
    # تجاهل الأوامر التي تبدأ بـ /
    if text.startswith("/"):
        return
        
    voice_key = context.user_data.get("selected_voice", "sa_f")
    voice_name = VOICES[voice_key]["voice"]
    
    status_msg = await update.message.reply_text("⏳ جاري توليد المقطع الصوتي...")
    
    output_file = f"voice_{update.message.from_user.id}.mp3"
    
    try:
        # تحويل النص إلى صوت باستخدام Edge-TTS
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(output_file)
        
        # إرسال الملف الصوتي للمستخدم
        with open(output_file, "rb") as audio:
            await update.message.reply_voice(voice=audio, caption=f"🗣️ النص: {text[:50]}...")
            
        await status_msg.delete()
        
    except Exception as e:
        logging.error(f"Error generating audio: {e}")
        await status_msg.edit_text("❌ حدث خطأ أثناء تحويل النص إلى صوت. حاول مجدداً.")
        
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
    app.run_polling()
