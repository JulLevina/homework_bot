import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from requests.exceptions import RequestException

from telegram import Bot, TelegramError

from dotenv import load_dotenv

import exceptions

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FORMAT = (
    '%(asctime)s - %(lineno)d - %(filename)s '
    '- %(name)s - %(levelname)s - %(message)s'
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 20  # 60 * 10
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
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
    except TelegramError as error:
        raise exceptions.SendingMessageReportError(
            'Сбой при отправке сообщения: '
            'проверьте корректность передаваемого '
            'токена и чат-id.'
        ) from error
    logger.info('Сообщение отправлено.')


def get_api_answer(current_timestamp: int) -> dict:
    """Получаем сведения о выполненных домашних работах за указанный период."""
    params = {'from_date': current_timestamp}
    logger.info(
        'Началась проверка данных для получения '
        'ответа от API Яндекс.Практикум.'
    )
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    except RequestException as error:
        raise exceptions.BadRequestError(
            'Ошибка неправильного запроса: '
        ) from error
    if response.status_code != HTTPStatus.OK:
        raise exceptions.NotOkStatusCodeError(
            f'Запрос не выполнен, статус ответа: {response.status_code}.'
        )
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as error:
        raise exceptions.DecodingFailsError(
            'В ответ передан пустой или недопустимый JSON.'
        ) from error
    finally:
        logger.info(
            'Проверка данных для получения '
            'ответа от API Яндекс.Практикум завершена.'
        )


def check_response(response: dict) -> dict:
    """Проверяем ответ API на корректность."""
    logger.info('Началась проверка ответа API на корректность.')
    if not isinstance(response, dict):
        raise TypeError(
            f'Указан некорректный тип данных: {response}. '
            f'Ожидаемый тип данных - словарь.'
        )
    if 'homeworks' not in response:
        raise exceptions.MissingKeyError(
            f'В ответе {response} отсутствует нужный ключ.'
        )
    homeworks_list = response['homeworks']
    if not homeworks_list:
        raise exceptions.NoNewChecksFromServer(
            'От сервера не поступила информация о новых проверках.'
        )
    if not isinstance(homeworks_list, list):
        raise exceptions.IncorrectTypeError(
            'Ожидаемый тип данных: список домашних работ.'
        )
    homework = homeworks_list[0]
    if 'current_date' not in response:
        raise exceptions.NoNewTimestampFromServer(
            'В ответе отсутствует временная метка.'
        )
    logger.info('Проверка ответа API на корректность завершена.')
    return homework


def parse_status(homework: dict) -> str:
    """Извлекаем из информации о домашней работе статус конкретного задания."""
    logger.info(
        'Идет получение статуса конкретного задания '
        'из информации о домашней работе.'
    )
    if 'homework_name' not in homework:
        raise KeyError(
            f'Словарь {homework} не содержит ключ homework_name.'
        )
    if 'status' not in homework:
        raise exceptions.UnknownHomeworkStatus(
            f'Словарь {homework} не содержит ключ status.'
        )
    homework_status = homework['status']
    homework_name = homework['homework_name']
    if homework_status not in HOMEWORK_VERDICTS:
        raise exceptions.UndocumentedHomeworkStatusError(
            'Указан недокументированный статус домашней работы!'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    logger.info('Получение статуса успешно завершено.')
    return (
        f'Изменился статус проверки работы "{homework_name}". '
        f'{verdict}'
    )


def check_tokens() -> bool:
    """Проверяем доступность переменных окружения."""
    logger.info('Началась проверка переменных окружения.')
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,))


def main() -> None:
    """Основная логика работы бота."""
    logger.info('Программа запущена!')
    if not check_tokens():
        message = 'Недоступна переменная окружения!'
        logger.critical(message)
        sys.exit(message)
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    message = new_message = str()
    while True:
        try:
            response = get_api_answer(current_timestamp=current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
        except exceptions.ErrorNotifications as exc:
            logger.error(exc)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        else:
            current_timestamp = response['current_date']
        if message != new_message:
            try:
                send_message(bot, message)
            except exceptions.SendingMessageReportError as error:
                logger.error(error)
            new_message = message
        else:
            logger.debug('Статус проверки домашней работы не изменился.')
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        format=FORMAT,
        level=logging.DEBUG,
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
        ],
        encoding='UTF-8'
    )
    try:
        main()
    except KeyboardInterrupt:
        logger.info('Работа программы завершена.')
