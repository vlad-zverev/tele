from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from .ai import AI


class Telegram:
    def __init__(self, ai: AI, token: str):
        self.ai = ai
        self.bot = ApplicationBuilder().token(token).build()
        for handler in [
            CommandHandler('start', self.start),
            MessageHandler(filters.TEXT & (~filters.COMMAND), self.talk_with_ai)
        ]:
            self.bot.add_handler(handler)

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Ask me anything...')

    async def talk_with_ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Let me think...')
        ai_response = await self.ai.complete(update.message.text)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=ai_response)

    def run(self):
        self.bot.run_polling()
