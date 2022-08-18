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


class SendMessageError(Exception):
    """Не получилось отправить сообщение."""

    def __init__(self, *args):
        """Формирует сообщение об ошибке."""
        if args:
            self.message = args[0]
        else:
            self.message = self.__doc__

    def __str__(self):
        """Выводит сообщение об ошибке."""
        return f'{self.message}'
