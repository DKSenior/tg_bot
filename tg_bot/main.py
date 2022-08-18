import logging
import sys
import telegram
import time

from homework import (get_api_answer, check_response, check_tokens,
                      parse_status, send_message)

from homework import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from messages import get_ip, get_time, wake_up, new_cat

from telegram.ext import Updater, CommandHandler

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(name)s - '
    '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
)
handler.setFormatter(formatter)

RETRY_TIME = 600


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(1)

    updater = Updater(token=TELEGRAM_TOKEN)
    updater.start_polling()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previous_status = None

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            result = check_response(response)
            if len(result) != 0:
                message = parse_status(result[0])
            else:
                message = 'За последнее время нет домашних заданий'
            logger.info(message)
            if message != previous_status:
                previous_status = message
                bot.send_chat_action(
                    chat_id=TELEGRAM_CHAT_ID,
                    action=telegram.ChatAction.TYPING
                )
                time.sleep(1)
                send_message(bot, message)
        except Exception as error:
            logger.error(error, exc_info=False)
            if str(error) != previous_status:
                previous_status = str(error)
                send_message(bot, str(error))
        finally:
            updater.dispatcher.add_handler(CommandHandler('start', wake_up))
            updater.dispatcher.add_handler(CommandHandler('kitty', new_cat))
            updater.dispatcher.add_handler(CommandHandler('time', get_time))
            updater.dispatcher.add_handler(CommandHandler('getip', get_ip))

            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format=('%(asctime)s - [%(levelname)s] - %(name)s - '
                '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s')
    )

    main()
