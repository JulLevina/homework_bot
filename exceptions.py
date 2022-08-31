class TelegramErrorNotifications(Exception):
    """Исключения, пересылаемые в телеграм-чат."""


class UnknownHomeworkStatus(TelegramErrorNotifications):
    """Статус проверки домашней работы не совпадает с ожидаемым."""


class UndocumentedHomeworkStatusError(TelegramErrorNotifications):
    """Указан недокументированный статус домашней работы."""


class NotOkStatusCodeError(TelegramErrorNotifications):
    """Запрос не выполнен."""


class SendingMessageReportError(TelegramErrorNotifications):
    """Сбой при отправке сообщения."""


class ErrorNotifications(Exception):
    """Ислючения, не пересылаемые в телеграм-чат."""


class StandartDeviations(ErrorNotifications):
    """Исключения при штатных отклонениях от основного сценария."""


class NoNewChecksFromServer(StandartDeviations):
    """От сервера не поступила информация о новых проверках."""


class NoNewTimestampFromServer(StandartDeviations):
    """От сервера не поступила новая временная метка."""
