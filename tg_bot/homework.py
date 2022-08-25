import logging
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv

from utils import (AnswerStatusIsNot200Error, IncorrectDataTypeError,
                   RequestReceivingError, SendMessageError)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(name)s - '
    '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
)
handler.setFormatter(formatter)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHATS_ID = os.getenv('TELEGRAM_CHATS_ID')

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    keys = (TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHATS_ID)
    check = True
    for key in keys:
        print(key)
        if key is None:
            logger.critical(f'Нет токена {key}')
            print(os.getenv('TMP'))
            check = False
    return True if check else False


def send_message(bot, message):
    """Отправляет сообщение в чат."""
    try:
        for TELEGRAM_CHAT_ID in TELEGRAM_CHATS_ID.split():
            logger.info('Бот начал отправлять сообщение.')
            bot.send_message(TELEGRAM_CHAT_ID, message)
            logger.info('Бот отправил сообщение')
    except Exception as error:
        raise SendMessageError(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """Отправляет запрос к эндпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        logger.info('Бот делает запрос к API')
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            raise AnswerStatusIsNot200Error(
                f'"{ENDPOINT} не отвечает. '
                f'Статус ответа: {response.status_code}'
            )
        return response.json()
    except Exception as error:
        raise RequestReceivingError(
            f'Ошибка при запросе к основному API: {error}'
        )


def check_response(response):
    """Проверяет ответ API на корректность."""
    logger.info('Проверка корректности ответа')
    if not isinstance(response, dict):
        logger.error(
            f'У ответа некорректный тип данных: {type(response)}'
        )

    try:
        homeworks = response['homeworks']
    except KeyError as error:
        raise KeyError(f'Отсутствует ключ homeworks: {error}')

    try:
        response['current_date']
    except KeyError as error:
        raise KeyError(f'Отсутствует ключ current_date: {error}')

    if not isinstance(homeworks, list):
        raise IncorrectDataTypeError(
            f'У ответа некорректный тип данных: {type(homeworks)}'
        )

    return homeworks


def parse_status(homework):
    """Извлекает из информации о домашке ее статус."""
    logger.info('Уточнение статуса проверки.')

    try:
        homework_name = homework['homework_name']
    except KeyError as error:
        raise KeyError(f'Отсутствует ключ homework_name: {error}')

    try:
        homework_status = homework['status']
    except KeyError as error:
        raise KeyError(f'Отсутствует ключ status: {error}')

    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as error:
        raise KeyError(
            f'Получен неизвестный статус проверки домашней работы.{error}'
        )

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'
