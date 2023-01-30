import asyncio
from uuid import uuid4

from speech_recognition import Recognizer, AudioFile, UnknownValueError
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from .ai import AI
from .utils import ogg_to_wav


class Telegram:
    def __init__(self, ai: AI, token: str):
        self.ai = ai
        self.recognizer = Recognizer()
        self.bot = ApplicationBuilder().token(token).build()
        for handler in [
            CommandHandler('start', self.start),
            MessageHandler(filters.TEXT & (~filters.COMMAND), self.talk_with_ai),
            MessageHandler(filters.VOICE, self.handle_voice),
        ]:
            self.bot.add_handler(handler)

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Ask me anything...'
        )

    async def talk_with_ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str = None):
        await self.send(update, context, 'Let me think...')
        msg = f'{text}?' if text else update.message.text
        ai_response, url = await asyncio.gather(
            self.ai.complete(msg),
            self.ai.image(request=msg),
        )
        await self.send(update, context, ai_response)
        await context.bot.send_photo(update.effective_chat.id, url)

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        path = f'voices/voice-{uuid4()}.ogg'
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive(path)
        wav_path = ogg_to_wav(path)
        with AudioFile(wav_path) as source:
            audio = self.recognizer.record(source)
        try:
            text = self.recognizer.recognize_google(audio, language='ru-RU')
            await self.send(update, context, f'So, you just say:\n\n{text}')
            await self.talk_with_ai(update, context, text)
        except UnknownValueError:
            await self.send(update, context, 'What did you say?\nRepeat, please')

    @staticmethod
    async def send(update: Update, context: ContextTypes.DEFAULT_TYPE, response: str):
        await context.bot.send_message(update.effective_chat.id, response)

    def run(self):
        self.bot.run_polling()
