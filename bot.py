import os
import telebot
import requests
import time

# البيانات الخاصة بك مدمجة مباشرة
BOT_TOKEN = "8376107764:AAEtXCa9kxco6oBXreJ5Ce_c_HhYv6Q-GG8"
ELEVENLABS_API_KEY = "sk_096000f591a15bd4337e537d67b1a31bfbac313f1085a7b7"
VOICE_ID = "albaa6OioIhKtKdCEkQw"

# إعداد البوت مع تحديد مهلة زمنية للاتصال لضمان عدم التعليق
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 مرحباً بك في بوت استنساخ وتحويل النصوص إلى صوت!\n\n"
        "🎙️ هذا البوت مخصص للتحدث بصوت فتاة سعودية.\n"
        "✍️ أرسل لي النص الذي تريد تحويله إلى صوت وسأقوم بمعالجته فوراً."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def convert_text_to_speech(message):
    text_to_speak = message.text
    
    if len(text_to_speak) > 400:
        bot.reply_to(message, "⚠️ النص طويل جداً! يرجى إرسال نص أقصر ليكون المقطع في حدود 30 ثانية.")
        return

    status_msg = bot.reply_to(message, "⏳ جاري معالجة النص وتحويله إلى صوت بالفتاة السعودية... انتظر لحظة.")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": text_to_speak,
        "model_id": "eleven_multilingual_v2",
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
            
            bot.delete_message(message.chat.id, status_msg.message_id)
            with open(audio_path, "rb") as audio:
                bot.send_voice(message.chat.id, audio, reply_to_message_id=message.message_id)
                
            if os.path.exists(audio_path):
                os.remove(audio_path)
        else:
            bot.edit_message_text("❌ عذراً، فشل توليد الصوت. تأكد من إعدادات حسابك في ElevenLabs.", message.chat.id, status_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"⚠️ حدث خطأ غير متوقع: {str(e)}", message.chat.id, status_msg.message_id)

if __name__ == "__main__":
    print("البوت بدأ العمل بنجاح...")
    # حلقة تكرارية ذكية لإعادة التشغيل تلقائياً في حال حدوث أي انقطاع في الاتصال بالسيرفر
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"حدث انقطاع مؤقت، جاري إعادة الاتصال: {e}")
            time.sleep(5)
