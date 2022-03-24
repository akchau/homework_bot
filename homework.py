
"""
Телеграм бот который отправит сообщение,
если изменился статус проверки домашней работы в Яндекс.Практикум."
"""

import os
import sys
from dotenv import load_dotenv
from telegram import Bot
import requests
import time
import logging

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
    )


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 0.2
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
TIME_OF_PRACTICUM_OPENING = 1549962000

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

MESSAGES = {
    'no_tokens': 'Ошибка токенов окружения. Завершение работы',
    'fail_api_request': 'Недоступен эндпоинт, ошибка АPI',
    'sent_message': 'Успешно отправлено сообщение в телеграмм',
    'many_failure': 'Превышено допустимое количество ошибок',
    'stop_bot': 'Бот остановлен!',
    'fail_api_response': 'API вернул некорректный ответ',
    'no_key_homeworks': 'В ответе нет ключа homeworks',
    'no_type_list': 'Некорректный тип данных ожидался list',
    'empty_list': 'За указанное время не было никаких домашек',
    'no_new_status': 'Статус работы не поменялся',
    'no_sent_message': 'Ошибка отправки сообщения',
    'no_documenting_status': 'Не задукоментрирован статус',
    'api_request_200': 'Код ответа - ОШИБКА'
}


class CodeApiError(Exception):
    """Исключение, когда в ответе API код не 200.

    Args:
        Exceptions (class): Базовый класс исключений
    """
    pass


class NoKeyHomeworks(Exception):
    """Исключение, когда в ответе API нет ключа homeworks.

    Args:
        Exceptions (class): Базовый класс исключений
    """
    pass


class NoTypeList(Exception):
    """Исключение, в ответе API тип данных не list.

    Args:
        Exceptions (class): Базовый класс исключений
    """
    pass


class EmptyList(Exception):
    """Исключение, в ответе API нет данных о домашке.

    Args:
        Exceptions (class): Базовый класс исключений
    """
    pass


def send_message(bot, message):
    """Функция отправляет сообщение от телеграм бота.

    Args:
        bot (Bot): Телеграмм клиент бота, авторизованный по токену
        message (str): Сообщение которое отправит бот
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        message = MESSAGES.get('no_sent_message')
        logging.error(message)
        print(message)
    else:
        message = MESSAGES.get('sent_message')
        logging.info(message)
        print(message)
    pass


def stop_bot():
    """Функция остановки бота
    """
    message_stop_bot = MESSAGES.get('stop_bot')
    logging.info(message_stop_bot)
    print(message_stop_bot)
    sys.exit(0)


def get_api_answer(current_timestamp) -> dict:
    """Функция делает запрос к API Яндекс.Практикум.

    Args:
        current_timestamp (int): Временная метка.

    Returns:
        list: Лист со всеми проверенными домашникми работами.
    """
    timestamp = current_timestamp or int(time.time())
    # timestamp = timestamp - TIME_OF_PRACTICUM_OPENING
    # timestamp = str(timestamp)
    params = {'from_date': timestamp}
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    response = requests.get(ENDPOINT, headers=headers, params=params)
    if response.status_code != 200:
        raise CodeApiError
    homeworks = response.json()
    return homeworks


def check_tokens() -> bool:
    """
    Проверяет наличие токенов в виртуальном окружении.
    Возвращает True, если все токены на месте"

    Returns:
        bool: True, если все токены в окружении на месте.
    """
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False


def check_telegram_tokens() -> bool:
    """
    Проверяет наличие только телеграмм токенов в виртуальном окружении.
    Возвращает True, если все токены на месте"

    Returns:
        bool: True, если все токены в окружении на месте.
    """
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False


def check_response(response: dict) -> dict:
    """Функция проверяет ответ API на:
    - Наличие ключа 'homeworks',
    - Тип данных dict,
    - Тип данных по ключу homeworks: list,

    Args:
        response (dict): Словарь который приходит в ответ от API.

    Raises:
        KeyError: В словаре нет ключа, по которому получим список работ.
        TypeError: _description_
        TypeError: _description_

    Returns:
        dict: Параметры посленей домашней работы
    """
    if 'homeworks' in response:
        if type(response.get('homeworks')) is not list:
            raise NoTypeList
        if len(response.get('homeworks')) == 0:
            raise EmptyList
    else:
        raise NoKeyHomeworks
    return response.get('homeworks')[0]


def parse_status(homework: dict) -> str:
    """Функция возвращает сообщение о изменении статуса проверки.

    Args:
        homework (dict): Словарь с параметрами домашней работы.

    Returns:
        str: Сообщение о изменении статуса проверки работы.
    """
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_status(homework: dict) -> str:
    """Функция получает на вход данные о ДЗ и возвращает статус"

    Args:
        homework (dict): Словарь с параметрами домашней работы.

    Returns:
        str: Статус последней домашней работы
    """
    return homework.get('status')


def api_incorrect(bot, message):
    logging.error(message)
    print(message)
    send_message(bot, message)
    pass


def main():
    """Главная функция!
    """
    current_timestamp = int(time.time())
    last_status = ''
    count_failure = 0
    message = MESSAGES.get('no_tokens')
    if check_telegram_tokens():
        bot = Bot(token=TELEGRAM_TOKEN)
        while check_tokens():
            if count_failure < 10:
                try:
                    response = get_api_answer(current_timestamp)
                except CodeApiError:
                    message = MESSAGES.get('api_request_200')
                    count_failure += 1
                    api_incorrect(bot, message)
                except Exception:
                    message = MESSAGES.get('fail_api_request')
                    count_failure += 1
                    api_incorrect(bot, message)
                else:
                    except_messages = {
                        NoKeyHomeworks: 'no_key_homeworks',
                        NoTypeList: 'no_type_list',
                        EmptyList: 'empty_list',
                        Exception: 'fail_api_response',
                    }
                    try:
                        homework = check_response(response)
                    except NoKeyHomeworks:
                        message = MESSAGES.get(except_messages[NoKeyHomeworks])
                        count_failure += 1
                        api_incorrect(bot, message)
                    except NoTypeList:
                        message = MESSAGES.get(except_messages[NoTypeList])
                        count_failure += 1
                        api_incorrect(bot, message)
                    except EmptyList:
                        message = MESSAGES.get(except_messages[EmptyList])
                        count_failure += 1
                        api_incorrect(bot, message)
                    except Exception:
                        message = MESSAGES.get(except_messages[Exception])
                        count_failure += 1
                        api_incorrect(bot, message, count_failure)
                    else:
                        current_stautus = check_status(homework)
                        if current_stautus == '':
                            message = MESSAGES.get('no_documenting_status')
                            count_failure += 1
                            logging.error(message)
                            print(message)
                            send_message(bot, message)
                        else:
                            if current_stautus != last_status:
                                message = parse_status(homework)
                                last_status = homework.get('status')
                                logging.info(message)
                                print(message)
                                send_message(bot, message)
                                time.sleep(RETRY_TIME)
                            else:
                                message = MESSAGES.get('no_new_status')
                                logging.debug(message)
                                print(message)
                finally:
                    time.sleep(RETRY_TIME)
            else:
                message = MESSAGES.get('many_failure')
                logging.critical(message)
                print(message)
                send_message(bot, message)
                stop_bot()
    else:
        logging.critical(message)
        print(message)
        stop_bot()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        stop_bot()
