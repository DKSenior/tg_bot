import logging
import os
import telegram
import time
import requests

from dotenv import load_dotenv
from http import HTTPStatus

logging.basicConfig(
    level=logging.INFO,
    format=('%(asctime)s - [%(levelname)s] - %(name)s - '
            '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s')
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
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
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Бот отправил сообщение')
    except Exception as error:
        logger.error(f'Сбой при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """Отправляет запрос к эндпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            raise Exception(f'Статус ответа {response.status_code}')
        return response.json()
    except ValueError as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')


def check_response(response):
    """Проверяет ответ API на корректность."""
    try:
        homeworks_list = response['homeworks']
    except KeyError as error:
        logger.error(f'Ошибка доступа по ключу homeworks: {error}')
    if homeworks_list is None:
        raise Exception('В ответе API нет словаря')
    if len(homeworks_list) == 0:
        raise Exception('За последнее время нет домашних заданий')
    if not isinstance(homeworks_list, list):
        raise Exception(
            'В ответе API домашние задания представлены не списком'
        )
    return homeworks_list[0]


def parse_status(homework):
    """Извлекает из информации о домашке ее статус."""
    try:
        homework_name = homework['homework_name']
    except TypeError as error:
        logger.error(f'Ошибка доступа по ключу homework_name: {error}')

    try:
        homework_status = homework['status']
    except KeyError:
        logger.error('На запрос статуса работы получен неизвестный статус.')

    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except Exception as error:
        logger.error(
            f'На запрос статуса работы получен неизвестный статус.{error}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствует необходимая переменная среды')
        raise Exception('Отсутствует необходимая переменная среды')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            result = check_response(response)
            message = parse_status(result)
            send_message(bot, message)
        except Exception as error:
            logger.error(error, exc_info=False)
            if str(error) != 'За последнее время нет домашних заданий':
                send_message(bot, str(error))

        current_timestamp = int(time.time())
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
