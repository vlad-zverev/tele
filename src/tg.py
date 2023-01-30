import asyncio
from uuid import uuid4

import openai
from speech_recognition import Recognizer, AudioFile, UnknownValueError
from telegram import Update, File, Message
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from .ai import AI
from .utils import ogg_to_wav, convert_image


class Telegram:
    def __init__(self, ai: AI, token: str):
        self.ai = ai
        self.recognizer = Recognizer()
        self.bot = ApplicationBuilder().token(token).build()
        for handler in [
            CommandHandler('start', self.start),
            MessageHandler(filters.TEXT & (~filters.COMMAND), self.talk_with_ai),
            MessageHandler(filters.VOICE, self.handle_voice),
            MessageHandler(filters.PHOTO, self.handle_image)
        ]:
            self.bot.add_handler(handler)
        self.thinking_sticker = 'CAACAgIAAxkBAAEcjy1j15qLCzHw8fZwiTOHzcs9-O_-mgACGAADwDZPE9b6J7-cahj4LQQ'

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='напиши мне что-нибудь... можно и голосовухой......'
        )

    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.send(update, context, 'обрабатываю пикчу.....')
        path = f'images/image-{uuid4()}.jpg'
        file_id = update.message.photo[-1].file_id
        await self.download_file(context, file_id, path)
        byte_array = convert_image(path)
        text = update.message.caption
        if text:
            await self.send(update, context, f'то есть, ты хочешь видоизменить картинку определенным образом...')
            url = await self.ai.image_edit(byte_array, text)
        else:
            url = await self.ai.image_variation(byte_array)
        await context.bot.send_photo(update.effective_chat.id, url)

    async def talk_with_ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str = None):
        greeting = await self.send(update, context, 'дай подумать...')
        sticker = await context.bot.send_sticker(update.effective_chat.id, self.thinking_sticker)
        msg = f'{text}?' if text else update.message.text
        ai_response, url = await asyncio.gather(
            self.ai.complete(msg),
            self.ai.image(request=msg),
        )
        await greeting.delete()
        await sticker.delete()
        await self.send(update, context, ai_response)
        if isinstance(url, str):
            await context.bot.send_photo(update.effective_chat.id, url)
        elif isinstance(url, openai.ErrorObject):
            await self.send(update, context, url)

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        path = f'voices/voice-{uuid4()}.ogg'
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive(path)
        wav_path = ogg_to_wav(path)
        with AudioFile(wav_path) as source:
            audio = self.recognizer.record(source)
        try:
            text = self.recognizer.recognize_google(audio, language='ru-RU')
            await self.send(update, context, f'так, ты только что сказал:\n\n{text}')
            await self.talk_with_ai(update, context, text)
        except UnknownValueError:
            await self.send(update, context, 'что ты сказал?\nне понял, повтори, плиз')

    @staticmethod
    async def download_file(context: ContextTypes.DEFAULT_TYPE, file_id: str, path: str) -> File:
        file = await context.bot.get_file(file_id, read_timeout=10)
        await file.download_to_drive(path)
        return file

    @staticmethod
    async def send(update: Update, context: ContextTypes.DEFAULT_TYPE, response: str) -> Message:
        return await context.bot.send_message(update.effective_chat.id, response)

    def run(self):
        self.bot.run_polling()
