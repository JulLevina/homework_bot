import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests

from telegram import Bot

from dotenv import load_dotenv

import exceptions


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 60 * 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter(FORMAT))
sh.setLevel(logging.DEBUG)
fh = RotatingFileHandler(
    'my_logger.log',
    encoding='UTF-8',
    maxBytes=50000000,
    backupCount=5
)
fh.setFormatter(logging.Formatter(FORMAT))
fh.setLevel(logging.DEBUG)
logger.addHandler(sh)
logger.addHandler(fh)


def send_message(bot, message):
    """Бот отправляет сообщение в чат со статусом домашней работы."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                     text=message
                     )


def get_api_answer(current_timestamp):
    """Получаем сведения о выполненных домашних работах за указанный период."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise exceptions.NotOkStatusCodeError(
            'Запрос не выполнен.'
        )
    else:
        return response.json()


def check_response(response):
    """Проверяем ответ API на корректность."""
    if not isinstance(response, dict):
        if response['homeworks'] not in response.keys():
            raise exceptions.ResponseApiKeyError(
                'Указан некорректный ключ.'
            )
    elif not isinstance(response['homeworks'], list):
        raise exceptions.ResponseApiTypeError(
            'Ожидаемый тип данных: список домашних работ.'
        )
    else:
        return response['homeworks']


def parse_status(homework):
    """Извлекаем из информации о домашней работе статус конкретного задания."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    try:
        homework_name is not None
    except KeyError as error:
        raise exceptions.UnknownHomeworkName(
            f'Название домашней работы не совпадает с ожидаемым. {error}'
        )
    try:
        homework_status is not None
    except KeyError as error:
        raise exceptions.UndocumentedHomeworkStatusError(
            f'Указан недокументированный статус домашней работы! {error}'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    return (
        f'Изменился статус проверки работы "{homework_name}".'
        f'{verdict}'
    )


def check_tokens():
    """Проверяем доступность переменных окружения."""
    vars_list = (
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    )
    for var in vars_list:
        return var


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        logger.info('Сообщение отправлено.')
    except exceptions.SendingMessageReportError as error:
        logger.error(f'Сбой при отправке сообщения: {error}')
    current_timestamp = int(time.time())
    if not check_tokens():
        message = 'Недоступна переменная окружения!'
        logger.critical(message)
    CURRENT_HOMEWORK_STATUS = ''
    while True:
        try:
            response = get_api_answer(current_timestamp=current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
        except IndexError as error:
            message = (
                f'Список работ пуст: {error}'
            )
            logger.debug(message)
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
            )
            if message != CURRENT_HOMEWORK_STATUS:
                send_message(bot, message)
                logger.info('Сообщение отправлено.')
                CURRENT_HOMEWORK_STATUS = message
            else:
                logger.info('Статус проверки домашней работы не изменился.')
                send_message(bot, message)
            time.sleep(RETRY_TIME)
        except exceptions.IncorrectApiAnswerError as error:
            message = (
                f'Сбой в работе программы: ошибка'
                f'при запросе к основному API! {error}'
            )
            logger.error(message)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                             text=message,
                             )
        except exceptions.ResponseApiTypeError as error:
            message = (
                f'Сбой в работе программы:'
                f'ожидаемый тип данных "список"! {error}')
            logger.error(message)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                             text=message,
                             )
        except exceptions.ResponseApiKeyError as error:
            message = (
                f'Сбой в работе программы: ошибка'
                f'при получении данных о выполненнных'
                f'домашних работах! {error}'
            )
            logger.error(message)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                             text=message,
                             )
        except exceptions.UnknownHomeworkName as error:
            message = (
                f'Сбой в работе программы: название'
                f'домашней работы не совпадает с ожидаемым. {error}'
            )
            logger.error(message)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                             text=message,
                             )
        except exceptions.UnknownHomeworkStatus as error:
            message = (
                f'Сбой в работе программы: статус проверки'
                f'домашней работы не совпадает с ожидаемым. {error}'
            )
            logger.error(message)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                             text=message,
                             )
        except exceptions.ParseStatusKeyError as error:
            message = (
                f'Сбой в работе программы:'
                f'словарь не содержит нужного ключа. {error}'
            )
            logger.error(message)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                             text=message,
                             )
        except exceptions.UndocumentedHomeworkStatusError as error:
            message = (
                f'Указан недокументированный статус домашней работы! {error}'
            )
            logger.error(message)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                             text=message,
                             )

        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='my_logger.log',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        encoding='UTF-8',
        filemode='w'
    )
    main()
