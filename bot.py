import os
import telebot
import requests

# البيانات الخاصة بك مدمجة مباشرة داخل الكود للسهولة
BOT_TOKEN = "8376107764:AAEtXCa9kxco6oBXreJ5Ce_c_HhYv6Q-GG8"
ELEVENLABS_API_KEY = "sk_096000f591a15bd4337e537d67b1a31bfbac313f1085a7b7"
VOICE_ID = "albaa6OioIhKtKdCEkQw"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 مرحباً بك في بوت استنساخ وتحويل النصوص إلى صوت!\n\n"
        "🎙️ هذا البوت مخصص للتحدث بصوت فتاة سعودية.\n"
        "✍️ أرسل لي النص الذي تريد تحويله إلى صوت (يُفضل أن يكون النص متوسط الطول للحصول على مقطع مدته 30 ثانية)."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def convert_text_to_speech(message):
    text_to_speak = message.text
    
    # شرط لضمان عدم إرسال نص طويل جداً يتجاوز مدة الـ 30 ثانية
    if len(text_to_speak) > 400:
        bot.reply_to(message, "⚠️ النص طويل جداً! يرجى إرسال نص أقصر (أقل من 70 كلمة) ليكون المقطع في حدود 30 ثانية.")
        return

    # إشعار المستخدم ببدء معالجة الصوت
    status_msg = bot.reply_to(message, "⏳ جاري معالجة النص وتحويله إلى صوت بالفتاة السعودية... انتظر لحظة.")
    
    # إعدادات الـ API الخاصة بـ ElevenLabs
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": text_to_speak,
        "model_id": "eleven_multilingual_v2",  # الموديل الذي يدعم اللهجات العربية بطلاقة
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.85
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            audio_path = "saudi_voice.mp3"
            with open(audio_path, "wb") as f:
                f.write(response.content)
            
            # حذف رسالة الانتظار وإرسال البصمة الصوتية للمخدم
            bot.delete_message(message.chat.id, status_msg.message_id)
            with open(audio_path, "rb") as audio:
                bot.send_voice(message.chat.id, audio, reply_to_message_id=message.message_id)
                
            # مسح الملف المؤقت من السيرفر للحفاظ على المساحة
            os.remove(audio_path)
        else:
            bot.edit_message_text("❌ عذراً، فشل توليد الصوت. تأكد من صلاحية حسابك في ElevenLabs.", message.chat.id, status_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"⚠️ حدث خطأ غير متوقع: {str(e)}", message.chat.id, status_msg.message_id)

if __name__ == "__main__":
    print("البوت يعمل الآن بصوت الفتاة السعودية...")
    bot.infinity_polling()
