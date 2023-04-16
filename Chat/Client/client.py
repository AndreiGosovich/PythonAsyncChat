import calendar
import json
import logging
import sys
from datetime import datetime, timezone
from socket import *

sys.path.append("../log")
import client_log_config

logger = logging.getLogger('chat.client')


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


def parse_server_response(data):
    logger.debug("Парсим ответ сервера")
    response_data = json.loads(data)

    return response_data


def get_socket(addr_family, socket_type):
    logger.debug("Создаём сокет")
    s = socket(addr_family, socket_type)  # Создать сокет TCP

    return s


def run_chat_client(addr='', port=7777):
    logger.debug("Запускаем клиент")
    if not addr:
        addr = ''
    if not port:
        port = 7777

    s = get_socket(AF_INET, SOCK_STREAM)
    s.connect((addr, port))  # Соединиться с сервером

    msg = create_presence_message('Andrei')

    logger.debug("Отправляем сообщение серверу")
    s.send(msg.encode('utf-8'))
    data = s.recv(1000000)
    logger.debug("Получили ответ сервера")

    server_response = parse_server_response(data.decode('utf-8'))

    logger.info(f'Сообщение от сервера: {server_response}, длиной {len(data)} байт')
    s.close()
    logger.debug("Закрываем соект. Работа клиента завершена.")


def main():
    logger.debug("Запуск клиента")
    args = get_arguments()

    run_chat_client(args[0], args[1])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical(e)
