import logging
import os
import sys

from dotenv import load_dotenv

from src import AI, Telegram

load_dotenv()

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'DEBUG'),
    format='%(asctime)s %(levelname)s (%(levelno)s) %(message)s',
    filename='bot.log',
)


if __name__ == '__main__':
    ai = AI(os.getenv('OPEN_AI_KEY'))
    bot = Telegram(ai, os.getenv('TELEGRAM_BOT_TOKEN'))
    bot.run()
