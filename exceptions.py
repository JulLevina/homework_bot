class IncorrectApiAnswerError(Exception):
    """Ошибка при запросе к основному API."""
    pass


class ResponseApiKeyError(Exception):
    """Ошибка при получении данных о выполненнных домашних работах"""
    pass


class ResponseApiTypeError(Exception):
    """Ожидаемый тип данных: список домашних работ."""
    pass


class UnknownHomeworkName(Exception):
    """Название домашней работы не совпадает с ожидаемым."""
    pass


class UnknownHomeworkStatus(Exception):
    """Статус проверки домашней работы не совпадает с ожидаемым."""
    pass


class ParseStatusKeyError(Exception):
    """Словарь HOMEWORK_STATUSES не содержит нужного ключа."""
    pass


class UndocumentedHomeworkStatusError(Exception):
    """Указан недокументированный статус домашней работы!"""
    pass


class NotOkStatusCodeError(Exception):
    """Запрос не выполнен."""


class CheckTokensError(Exception):
    """Недоступна переменная окружения!"""
    pass


class SendingMessageReportError(Exception):
    """Сбой при отправке сообщения."""
    pass
