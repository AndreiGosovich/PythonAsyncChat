import calendar
import inspect
import json
import logging
import sys
from datetime import datetime, timezone
from socket import *
from functools import wraps
from select import select

sys.path.append("../log")
import client_log_config

logger = logging.getLogger('chat.client')


def log():
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            logger.info(f' Функция {func.__name__} вызвана из функции {inspect.stack()[1].function}')
            res = func(*args, **kwargs)
            return res

        return decorated

    return decorator


@log()
def get_arguments():
    logger.debug('Получаем аргументы')
    args = sys.argv
    if len(args) > 1:
        addr = args[1]
    else:
        raise SystemExit('Invalid address')

    port = 0
    if len(args) > 2:
        port = int(args[2])

    logger.info(f'address = {addr}, port = {port}')
    return addr, port


@log()
def create_presence_message(account_name, status='online', _type='status'):
    logger.debug("Создаём сообщение серверу")
    return json.dumps({
        "action": "presence",
        "time":  calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
        "type": _type,
        "user": {
            "account_name": account_name,
            "status": status,
        }
    })


@log()
def create_text_message(to_user, from_user, message, encoding='utf-8'):
    # logger.debug("Создаём сообщение серверу")
    return json.dumps({
        "action": "msg",
        "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
        "to": to_user,
        "from": from_user,
        "encoding": encoding,
        "message": message,
    })


@log()
def parse_server_response(data):
    # logger.debug("Парсим ответ сервера")
    response_data = json.loads(data)

    if 'action' in response_data and response_data['action'] == 'msg':
        response_data = f'Получено сообщение от пользователя {response_data["to"]}: {response_data["message"]}'

    return response_data


@log()
def get_socket(addr_family, socket_type):
    # logger.debug("Создаём сокет")
    s = socket(addr_family, socket_type)  # Создать сокет TCP

    return s


@log()
def run_chat_client(addr='', port=7777):
    # logger.debug("Запускаем клиент")
    if not addr:
        addr = ''
    if not port:
        port = 7777

    with get_socket(AF_INET, SOCK_STREAM) as s:
        s.connect((addr, port))  # Соединиться с сервером
        msg = create_presence_message('Andrei')
        # logger.debug("Отправляем Presense сообщение серверу")
        s.send(msg.encode('utf-8'))
        data = s.recv(1000000).decode('utf-8')
        # logger.debug("Получили ответ сервера")
        server_response = parse_server_response(data)
        # logger.info(f'Сообщение от сервера: {server_response}, длиной {len(data)} байт')
        msg = ''
        while True:
            if msg != 'listen':
                msg = input('Ваше сообщение: ')
                if msg == 'exit':
                    break
                elif msg == 'presence':
                    msg = create_presence_message('Andrei')
                elif msg == 'listen':
                    data = s.recv(1000000)  # Очистить очередь
                else:
                    msg = create_text_message("Andrei", "ALL", msg)

                if msg != 'listen':
                    s.send(msg.encode('utf-8'))  # Отправить!
            else:
                data = s.recv(1000000).decode('utf-8')
                if data:
                    server_response = parse_server_response(data)
                    logger.info(f'Сообщение от сервера: {server_response}, длиной {len(data)} байт')
                else:
                    logger.critical("Server close connection")
                    s.close()
                    break


@log()
def main():
    logger.debug("Запуск клиента")
    args = get_arguments()

    run_chat_client(args[0], args[1])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical(e)
