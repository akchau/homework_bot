"""Телеграм бот который отправит сообщения.
если изменился статус проверки домашней работы в Яндекс.Практикум."
"""

import os
import sys
from dotenv import load_dotenv
from telegram import Bot
import requests
import time
import logging
from exceptions import exceptions
from logging.handlers import RotatingFileHandler
from http import HTTPStatus

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'my_logger.log',
    maxBytes=50000000,
    backupCount=5
)
logger.addHandler(handler)
handler.setFormatter(formatter)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TOKENS = [TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN]
TELEGRAM_TOKENS = [TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]


RETRY_TIME = 20
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
TIME_OF_PRACTICUM_OPENING = 1549962000

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

INFO_MESSAGES = {
    'sent_message': 'Успешно отправлено сообщение в телеграмм',
    'stop_bot': 'Бот остановлен!',
    'no_new_status': 'Статус работы не поменялся',
}


UNIVERSE_EXCEPT_MESSAGES = {
    'no_sent_message': 'Ошибка отправки сообщения',
    'fail_api_response': 'API вернул некорректный ответ',
    'no_tokens': 'Ошибка токенов окружения. Завершение работы',
    'fail_api_request': 'Недоступен эндпоинт, ошибка запроса к АPI',
    'many_failure': 'Превышено допустимое количество ошибок / ошибка токенов.',
}


def check_tokens():
    """Функция проверяет наличие токенов.

    Returns:
        _type_: _description_
    """
    # Для ревьюера: Если объеденить их в одну переменную - не проходят тесты.
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def get_api_answer(current_timestamp) -> dict:
    """Функция делает запрос к API Яндекс.Практикум.

    Args:
        current_timestamp (int): Временная метка.

    Returns:
        list: Лист со всеми проверенными домашникми работами.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    response = requests.get(ENDPOINT, headers=headers, params=params)
    if response.status_code != HTTPStatus.OK:
        raise exceptions.CodeApiError
    homeworks = response.json()
    return homeworks


def check_response(response: dict) -> dict:
    """Функция проверяет ответ API.
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
    if isinstance(response, dict):
        if 'homeworks' in response:
            if isinstance(response.get('homeworks'), list):
                return response.get('homeworks')[0]
            raise TypeError('API возвращает не список.')
        raise KeyError('В ответе нет ключа homeworks.')
    raise TypeError('API возвращает не словарь.')


def check_status(homework: dict) -> str:
    """Функция получает на вход данные о ДЗ и возвращает статус.

    Args:
        homework (dict): Словарь с параметрами домашней работы.

    Returns:
        str: Статус последней домашней работы
    """
    return homework.get('status')


def parse_status(homework: dict) -> str:
    """Функция возвращает сообщение о изменении статуса проверки.

    Args:
        homework (dict): Словарь с параметрами домашней работы.

    Returns:
        str: Сообщение о изменении статуса проверки работы.
    """
    text = 'Изменился статус проверки работы "{s}". {v}'
    if isinstance(homework, dict):
        if 'status' in homework:
            if 'homework_name' in homework:
                if isinstance(homework.get('status'), str):
                    homework_name = homework.get('homework_name')
                    homework_status = homework.get('status')
                    verdict = HOMEWORK_STATUSES.get(homework_status)
                    return text.format(s=homework_name, v=verdict)
                raise TypeError('Cтатус не str.')
            raise KeyError('В ответе нет ключа homework_name.')
        raise KeyError('В ответе нет ключа status.')
    raise KeyError('API возвращает не словарь.')


def send_message(bot, message):
    """Функция отправляет сообщение от телеграм бота.

    Args:
        bot (Bot): Телеграмм клиент бота, авторизованный по токену
        message (str): Сообщение которое отправит бот
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        message = UNIVERSE_EXCEPT_MESSAGES.get('no_sent_message')
        logging.error(message)
    else:
        message = INFO_MESSAGES.get('sent_message')
        logging.info(message)
    pass


def stop_bot():
    """Функция остановки бота."""
    message_stop_bot = INFO_MESSAGES.get('stop_bot')
    logging.info(message_stop_bot)
    sys.exit(0)


def main():
    """Главная функция."""
    current_timestamp = int(time.time() - TIME_OF_PRACTICUM_OPENING)
    logging.info('Бот запущен')
    last_status: str = ''
    count_failure = 0
    message = UNIVERSE_EXCEPT_MESSAGES.get('no_tokens')
    if TELEGRAM_TOKENS:
        bot = Bot(token=TELEGRAM_TOKEN)
        while check_tokens() and count_failure < 3:
            try:
                response = get_api_answer(current_timestamp)
            except Exception as error:
                error_message = UNIVERSE_EXCEPT_MESSAGES.get(
                    'fail_api_request')
                logging.error(f'Ошибка: {error_message} - {error}')
                count_failure += 1
                continue
            try:
                homework = check_response(response)
            except Exception as error:
                error_message = UNIVERSE_EXCEPT_MESSAGES.get(
                    'fail_api_response')
                logging.error(f'{error_message} - {error}')
                count_failure += 1
                continue
            current_stautus = check_status(homework)
            if current_stautus != last_status:
                try:
                    message = parse_status(homework)
                except Exception as error:
                    error_message = UNIVERSE_EXCEPT_MESSAGES.get(
                        'fail_api_response')
                    logging.error(f'{error_message} - {error}')
                    count_failure += 1
                    continue
                last_status = current_stautus
                logging.info(message)
                send_message(bot, message)
            else:
                message = INFO_MESSAGES.get('no_new_status')
                logging.debug(message)
            time.sleep(RETRY_TIME)
        else:
            message = UNIVERSE_EXCEPT_MESSAGES.get('many_failure')
            send_message(bot, message)
    logging.critical(message)
    stop_bot()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        stop_bot()
