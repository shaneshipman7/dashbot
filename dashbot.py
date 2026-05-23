from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = "8538746974:AAGRC_xfBUVXm0A8Myh2EBNdQgm1H9hsHSs"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"✅ /start received from chat {update.message.chat.id}")
    await update.message.reply_text("✅ Hello! I'm online and working.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    print(f"📨 Message received: {text}")
    await update.message.reply_text(f"You said: {text}")

if __name__ == "__main__":
    print("🚀 Bot is running... Keep this window OPEN!")
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    app.run_polling()