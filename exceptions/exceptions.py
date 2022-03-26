class NoTypeStr(Exception):
    """Исключение, статус домашки тип данных не str.

    Args:
        Exceptions (class): Базовый класс исключений
    """
    def __init__(self, message='Ожидался str со статусом.'):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class NullStatus(Exception):
    """Исключение, когда в статус незадокументирован.

    Args:
        Exceptions (class): Базовый класс исключений
    """

    def __init__(self, message='Пустой статус домашки.'):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class NoTypeDict(Exception):
    """Исключение, когда в ответе API код не 200.

    Args:
        Exceptions (class): Базовый класс исключений
    """
    def __init__(self, message='Ожидался dict с домашкой.'):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class CodeApiError(Exception):
    """Исключение, когда в ответе API код не 200.

    Args:
        Exceptions (class): Базовый класс исключений
    """
    def __init__(self, message='Код ответа НЕ 200.'):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class NoKeyHomeworks(Exception):
    """Исключение, когда в ответе API нет ключа homeworks.

    Args:
        Exceptions (class): Базовый класс исключений
    """
    def __init__(self, message='В ответе нет ключа homeworks.'):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class NoTypeList(Exception):
    """Исключение, в ответе API тип данных не list.

    Args:
        Exceptions (class): Базовый класс исключений
    """
    def __init__(self, message='Ожидался list с домашками.'):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class EmptyList(Exception):
    """Исключение, в ответе API нет данных о домашке.

    Args:
        Exceptions (class): Базовый класс исключений
    """
    def __init__(self, message='Увеличьте время.'):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
