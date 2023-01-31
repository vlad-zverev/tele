import asyncio
import logging
from uuid import uuid4

from gtts import gTTS
import openai
from speech_recognition import Recognizer, AudioFile, UnknownValueError
from telegram import Update, File, Message, ReplyKeyboardMarkup, Voice
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from .ai import AI
from .utils import ogg_to_wav, convert_image
from typing import Any
import json
from enum import Enum


class State(Enum):
    START = 'start'
    CONVERSATION = 'conversation'


class SessionsHandler:
    def __init__(self):
        self.sessions: dict[int, dict] = {}
        self.save_sessions()
        self.load_sessions()

    def get_session(self, user_id: int):
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                'state': State.START.value,
                'data': {},
            }
        return self.sessions[user_id]

    def update_session(self, user_id: int, state: State, data: Any):
        self.sessions[user_id] = {
            'state': state,
            'data': data
        }

    def delete_session(self, user_id: int):
        if user_id in self.sessions:
            del self.sessions[user_id]

    def save_sessions(self, file_name: str = 'sessions.json'):
        with open(file_name, 'w+') as f:
            if self.sessions:
                json.dump(self.sessions, f)

    def load_sessions(self, file_name: str = 'sessions.json'):
        with open(file_name, 'r') as f:
            if f.buffer.read():
                self.sessions = json.load(f)


class Telegram:
    def __init__(self, ai: AI, token: str):
        self.ai = ai
        self.recognizer = Recognizer()
        self.bot = ApplicationBuilder().token(token).build()
        self.sessions_handler = SessionsHandler()
        for handler in [
            CommandHandler('start', self.start),
            MessageHandler(filters.TEXT & filters.Regex('забудь всё'), self.forget),
            MessageHandler(filters.TEXT & (~filters.COMMAND), self.talk_with_ai),
            MessageHandler(filters.VOICE, self.handle_voice),
            MessageHandler(filters.PHOTO, self.handle_image),
        ]:
            self.bot.add_handler(handler)
        self.thinking_sticker = 'CAACAgIAAxkBAAEcjy1j15qLCzHw8fZwiTOHzcs9-O_-mgACGAADwDZPE9b6J7-cahj4LQQ'

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='напиши мне что-нибудь... можно и голосовухой......'
        )

    async def forget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.sessions_handler.delete_session(update.effective_chat.id)
        await self.send(update, context, 'ладно...... забыл про тебя')

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
        msg = text or update.message.text
        state = self.sessions_handler.get_session(update.effective_chat.id)
        if state['state'] == State.CONVERSATION.value:
            msg = state['data']['dialogue'][-500:] + f'\n{msg}'
        greeting = await self.send(update, context, 'дай подумать...', disable_notification=True)
        sticker = await context.bot.send_sticker(update.effective_chat.id, self.thinking_sticker, disable_notification=True)
        ai_response, url = await asyncio.gather(
            self.ai.complete(msg),
            self.ai.image(request=msg),
        )
        state['state'] = State.CONVERSATION.value
        state['data']['dialogue'] = f'{msg}\n{ai_response}'
        self.sessions_handler.save_sessions()
        logging.info(state)
        await asyncio.gather(
            greeting.delete(),
            sticker.delete(),
            self.send(update, context, ai_response),
        )
        if isinstance(url, str):
            await context.bot.send_photo(update.effective_chat.id, url)
        elif isinstance(url, openai.ErrorObject):
            await self.send(update, context, str(url))
        path = f"voices/speech-{uuid4()}.ogg"
        speech = gTTS(text=ai_response, lang='ru')
        speech.save(path)
        await context.bot.send_voice(
            chat_id=update.message.chat_id,
            voice=open(path, 'rb'),
            duration=60,
            disable_notification=True,
        )

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        path = f'voices/voice-{uuid4()}.ogg'
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive(path)
        wav_path = ogg_to_wav(path)
        with AudioFile(wav_path) as source:
            audio = self.recognizer.record(source)
        try:
            text = self.recognizer.recognize_google(audio, language='ru-RU')
            await self.send(update, context, f'так, ты только что сказал:\n\n{text}', disable_notification=True)
            await self.talk_with_ai(update, context, text)
        except UnknownValueError:
            await self.send(update, context, 'что ты сказал?\nне понял, повтори, плиз')

    @staticmethod
    async def download_file(context: ContextTypes.DEFAULT_TYPE, file_id: str, path: str) -> File:
        file = await context.bot.get_file(file_id, read_timeout=10)
        await file.download_to_drive(path)
        return file

    @staticmethod
    async def send(
            update: Update, context: ContextTypes.DEFAULT_TYPE,
            response: str, keyboard: ReplyKeyboardMarkup = None,
            disable_notification: bool = None,
    ) -> Message:
        if not keyboard:
            keyboard = ReplyKeyboardMarkup([['забудь всё']], one_time_keyboard=True, resize_keyboard=True)
        return await context.bot.send_message(
            update.effective_chat.id, response,
            reply_markup=keyboard,
            disable_notification=disable_notification,
        )

    def run(self):
        self.bot.run_polling()
