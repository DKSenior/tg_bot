import logging
import os
import sys
import telegram
import time
import requests

from dotenv import load_dotenv
from http import HTTPStatus

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
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class AnswerStatusIsNot200Error(Exception):
    """Статус ответа не равен значению 200."""

    def __init__(self, *args):
        """Формирует сообщение об ошибке."""
        if args:
            self.message = args[0]
        else:
            self.message = self.__doc__

    def __str__(self):
        """Выводит сообщение об ошибке."""
        return f'{self.message} '


class RequestReceivingError(Exception):
    """Ошибка получения ответа на запрос."""

    def __init__(self, *args):
        """Формирует сообщение об ошибке."""
        if args:
            self.message = args[0]
        else:
            self.message = self.__doc__

    def __str__(self):
        """Выводит сообщение об ошибке."""
        return f'{self.message}'


class IncorrectDataTypeError(Exception):
    """Некорректные тип данных в ответе."""

    def __init__(self, *args):
        """Формирует сообщение об ошибке."""
        if args:
            self.message = args[0]
        else:
            self.message = self.__doc__

    def __str__(self):
        """Выводит сообщение об ошибке."""
        return f'{self.message}'


def send_message(bot, message):
    """Отправляет сообщение в чат."""
    try:
        logger.info('Бот начал отправлять сообщение.')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Бот отправил сообщение')
    except Exception as error:
        raise Exception(f'Ошибка при отправке сообщения: {error}')


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

    # if not isinstance(response, dict):
    #     raise IncorrectDataTypeError(
    #         f'У ответа некорректный тип данных: {type(response)}'
    #     )

    try:
        homeworks = response['homeworks']
    except KeyError as error:
        raise KeyError(f'Ошибка доступа по ключу homeworks: {error}')

    try:
        response['current_date']
    except KeyError as error:
        raise KeyError(f'Ошибка доступа по ключу current_date: {error}')

    if not isinstance(homeworks, list):
        raise IncorrectDataTypeError(
            'В ответе API домашние задания представлены не списком'
        )
    if homeworks is None:
        raise Exception('В ответе API нет словаря')

    return homeworks


def parse_status(homework):
    """Извлекает из информации о домашке ее статус."""
    logger.info('Уточнение статуса проверки.')

    try:
        homework_name = homework['homework_name']
    except KeyError as error:
        raise KeyError(f'Ошибка доступа по ключу homework_name: {error}')

    try:
        homework_status = homework['status']
    except KeyError as error:
        raise KeyError(f'Ошибка доступа по ключу status: {error}')

    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as error:
        raise KeyError(
            f'Получен неизвестный статус проверки домашней работы.{error}'
        )

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    keys = [TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN]
    check = True
    for key in keys:
        if key is None:
            logger.critical(f'Нет токена {key}')
            check = False
    return check


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previous_status = None
    previous_error = None

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response['current_date']
            result = check_response(response)
            if len(result) != 0:
                message = parse_status(result[0])
            else:
                message = 'За последнее время нет домашних заданий'
            logger.info(message)
            status = message
            if status != previous_status:
                previous_status = status
                send_message(bot, message)
        except Exception as error:
            if str(error) != previous_error:
                previous_error = str(error)
                logger.error(error, exc_info=True)
                send_message(bot, str(error))
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format=('%(asctime)s - [%(levelname)s] - %(name)s - '
                '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s')
    )

    main()
