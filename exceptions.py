class TelegramErrorNotifications(Exception):
    """Исключения, пересылаемые в телеграм-чат."""


class UnknownHomeworkStatus(Exception):
    """Статус проверки домашней работы не совпадает с ожидаемым."""


class UndocumentedHomeworkStatusError(Exception):
    """Указан недокументированный статус домашней работы."""


class BadRequestError(Exception):
    """Ошибка неправильного запроса."""


class NotOkStatusCodeError(Exception):
    """Запрос не выполнен."""


class DecodingFailsError(Exception):
    """В ответ передан пустой или недопустимый JSON."""


class MissingKeyError(Exception):
    """В словаре отсутствует нужный ключ."""


class IncorrectTypeError(Exception):
    """Указан некорректный тип данных: ожидаемый тип данных - список."""


class ErrorNotifications(Exception):
    """Ислючения, не пересылаемые в телеграм-чат."""


class SendingMessageReportError(ErrorNotifications):
    """Сбой при отправке сообщения."""


class StandartDeviations(ErrorNotifications):
    """Исключения при штатных отклонениях от основного сценария."""


class NoNewChecksFromServer(StandartDeviations):
    """От сервера не поступила информация о новых проверках."""


class NoNewTimestampFromServer(StandartDeviations):
    """От сервера не поступила новая временная метка."""
