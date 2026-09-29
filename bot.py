import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ضع توكن البوت الخاص بك من BotFather بين التنصيص هنا
BOT_TOKEN = "8727272025:AAHZlD6qmL6l4JpteY2OUTdReOFV6d6eh3I"

# ضع مفتاح Replicate API الخاص بك بين التنصيص هنا
REPLICATE_API_TOKEN = "r8_bjHiDVk5xfwoUa0lXenhg6jvqKtZOMF0IwEDE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك! 👋\n\n"
        "أنا بوت الذكاء الاصطناعي لتوليد الفيديوهات.\n"
        "أرسل الأمر /video متبوعاً بالوصف الذي تريده لتوليد فيديو.\n\n"
        "مثال:\n`/video فتاة تتحدث وتقول مساء الخير`",
        parse_mode="Markdown"
    )

async def generate_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ يرجى كتابة وصف الفيديو بعد الأمر.\nمثال:\n`/video فتاة تتحدث وتقول مرحباً`", parse_mode="Markdown")
        return

    prompt = " ".join(context.args)
    status_msg = await update.message.reply_text("⏳ جاري معالجة طلبك وتوليد الفيديو، يرجى الانتظار...")

    try:
        headers = {
            "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json={
                "version": "3f042d3237730042613be5d42b3786230f6d3733",
                "input": {"prompt": prompt}
            }
        )
        
        if response.status_code == 201:
            await status_msg.edit_text("✅ تم إرسال الطلب للذكاء الاصطناعي، يكتمل التوليد خلال لحظات...")
        else:
            await status_msg.edit_text("❌ حدث خطأ أثناء التواصل مع سيرفر الذكاء الاصطناعي. تأكد من مفتاح Replicate API.")

    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ غير متوقع: {str(e)}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("video", generate_video))
    app.run_polling()

if __name__ == '__main__':
    main()
