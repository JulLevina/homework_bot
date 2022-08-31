import logging
import os
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
from requests.exceptions import RequestException

from telegram import Bot, TelegramError

from dotenv import load_dotenv

import exceptions

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 60 * 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


def send_message(bot: Bot, message: str) -> None:
    """Бот отправляет сообщение в чат со статусом домашней работы."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                         text=message)
    except TelegramError as error:
        raise exceptions.SendingMessageReportError(
            'Сбой при отправке сообщения:'
            'проверьте корректность передаваемого'
            'токена и чат-id.') from error
    logger.info('Сообщение отправлено.')


def get_api_answer(current_timestamp: int) -> dict:
    """Получаем сведения о выполненных домашних работах за указанный период."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        logger.info(
            'Началась проверка данных для получения '
            'ответа от API Яндекс.Практикум.')
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    except RequestException as error:
        raise exceptions.NotOkStatusCodeError(
            'Запрос не выполнен.') from error
    if response.status_code != HTTPStatus.OK:
        raise exceptions.NotOkStatusCodeError(
            f'Запрос не выполнен, статус ответа: {response.status_code}.')
    logger.info('Проверка данных для получения '
                'ответа от API Яндекс.Практикум завершена.')
    return response.json()


def check_response(response: dict) -> dict:
    """Проверяем ответ API на корректность."""
    logger.info('Началась проверка ответа API на корректность.')
    if not isinstance(response, dict):
        raise TypeError(
            f'Указан некорректный тип данных: {response}.'
            f'Ожидаемый тип данных - словарь.'
        )
    homeworks_list = response['homeworks']
    if 'homeworks' not in response:
        raise exceptions.StandartDeviations(
            f'В ответе {response} отсутствует нужный ключ.')
    if 'current_date' not in response:
        raise exceptions.NoNewTimestampFromServer(
            'В ответе отсутствует временная метка.')
    if not isinstance(homeworks_list, list):
        raise exceptions.StandartDeviations(
            'Ожидаемый тип данных: список домашних работ.')
    try:
        homework = homeworks_list[0]
    except IndexError as error:
        raise exceptions.NoNewChecksFromServer(
            'От сервера не поступила информация о новых проверках.') from error
    logger.info('Проверка ответа API на корректность завершена.')
    return homework


def parse_status(homework: dict) -> str:
    """Извлекаем из информации о домашней работе статус конкретного задания."""
    logger.info('Идет получение статуса конкретного задания '
                'из информации о домашней работе.')
    if 'homework_name' not in homework:
        raise KeyError(
            'Название домашней работы не совпадает с ожидаемым.'
        )
    if 'status' not in homework:
        raise exceptions.UnknownHomeworkStatus(
            'Статус проверки домашней работы не совпадает с ожидаемым.')
    homework_status = homework['status']
    homework_name = homework['homework_name']
    if homework_status not in HOMEWORK_VERDICTS:
        raise exceptions.UndocumentedHomeworkStatusError(
            'Указан недокументированный статус домашней работы!'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    logger.info('Получение статуса успешно завершено.')
    return (
        f'Изменился статус проверки работы "{homework_name}".'
        f'{verdict}'
    )


def check_tokens() -> True:
    """Проверяем доступность переменных окружения."""
    logger.info('Началась проверка переменных окружения.')
    vars_list = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    ]
    if all(vars_list):
        logger.info('Проверка успешно завершена.')
        return True


def main() -> None:
    """Основная логика работы бота."""
    logger.info('Программа запущена!')
    if not check_tokens():
        message = 'Недоступна переменная окружения!'
        logger.critical(message)
        sys.exit(message)
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    current_homework_status = ''
    new_error_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp=current_timestamp)
            homework = check_response(response)
            if current_homework_status != homework['status']:
                message = parse_status(homework)
                send_message(bot, message)
                current_homework_status = homework['status']
            else:
                message = ('Статус проверки домашней работы не изменился.')
                logger.debug(message)
            time.sleep(RETRY_TIME)
        except exceptions.ErrorNotifications as exc:
            logger.error(exc)
        except exceptions.TelegramErrorNotifications as error:
            message = (
                f'Сбой в работе программы: {error}'
            )
            logger.error(message)
            if new_error_message != message:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                                 text=message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        filename=os.path.join(BASE_DIR, 'my_logger.log'),
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG,
        encoding='UTF-8'
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(lineno)d - %(filename)s '
        '- %(name)s - %(levelname)s - %(message)s')
    handler_1 = logging.StreamHandler(stream=sys.stdout)
    handler_2 = RotatingFileHandler(
        (os.path.join(BASE_DIR, 'my_logger.log')),
        encoding='UTF-8',
        maxBytes=150_000,
        backupCount=5)
    handler_1.setFormatter(formatter)
    handler_2.setFormatter(formatter)
    logger.addHandler(handler_1)
    logger.addHandler(handler_2)
    main()
