import datetime
import logging
import requests


from telegram import ReplyKeyboardMarkup

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(name)s - '
    '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
)
handler.setFormatter(formatter)


def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = ReplyKeyboardMarkup([
        ['/start', '/kitty'],
        ['/time', '/myip']
    ], resize_keyboard=True)
    context.bot.send_message(
        chat_id=chat.id,
        text=f'Привет! Рад тебя видеть, {name}!\n\n '
             'Напиши мне команду:\n'
             '/kitty - я пришлю фото котика\n'
             '/time - если нужно уточнить точное время (по серверу)\n'
             '/myip - если хочешь узнать свой IP\n'
             '/start - я пришлю инструкцию',
        reply_markup=button
    )


def get_new_image():
    url = 'https://api.thecatapi.com/v1/images/search'

    try:
        response = requests.get(url)
    except Exception as error:
        logging.error(f'Ошибка при запросе к {url}: {error}')
        new_url = 'https://api.thedogapi.com/v1/images/search'
        response = requests.get(new_url)

    response = response.json()
    random_cat = response[0].get('url')
    return random_cat


def new_cat(update, context):
    try:
        chat = update.effective_chat
        context.bot.send_photo(chat.id, get_new_image())
    except Exception as error:
        logger.error(f'Невозможно получить картинку: {error}')


def get_time(update, context):
    date = update.message.date.strftime("%H:%M:%S")
    chat = update.effective_chat
    message = f'Текущее время по северу: {date}'

    try:
        context.bot.send_message(chat.id, text=message)
    except Exception as error:
        logger.error(f'Не получилось узнать время: {error}')


def get_ip(update, context):
    url = 'https://api.ipify.org/'

    try:
        response = requests.get(url).text
        chat = update.effective_chat
        context.bot.send_message(chat.id, text=response)
    except Exception as error:
        logging.error(f'Ошибка при запросе к {url}: {error}')




