import argparse
import calendar
from socket import *
import json
from datetime import datetime, timezone
import sys
import logging

sys.path.append("../log")
import server_log_config
logger = logging.getLogger('chat.server')


def get_arguments():
    logger.debug('Получаем аргументы')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='port', type=int, help='Port of server run. Default 7777')
    parser.add_argument('-a', dest='addr', type=str, help='PIP-address listen to. Default ALL')
    args = parser.parse_args()
    logger.info(f'address = {args.addr}, port = {args.port}')
    return args.addr, args.port


def get_socket(addr, port):
    logger.debug("Создаём сокет")
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((addr, port))

    return s


def parse_client_data(data):
    logger.debug("Парсим сообщение от клиента")
    client_data = json.loads(data)

    return client_data


def get_response(client_data):
    logger.debug("Формируем ответ клиенту")
    action = client_data['action']

    code = 400
    alert = 'Неправильный запрос'

    if action == 'presence':
        code = 200
        alert = 'Ok'

    response = {
            "response": code,
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "alert": alert,
        }

    return json.dumps(response)


def run_chat_server(addr='', port=7777):
    logger.debug("Запускаем сервер")
    if not addr:
        addr = ''
    if not port:
        port = 7777

    s = get_socket(addr, port)
    logger.debug("Слушаем сокет")
    s.listen(5)
    
    while True:
        client, addr = s.accept()
        data = client.recv(1000000).decode('utf-8')

        logger.info(f'Получено сообщение:\n{data}\nот Клиента с адреса: {addr}')

        client_data = parse_client_data(data)

        response_data = get_response(client_data)

        logger.debug("Отправляем ответ клиенту")
        client.send(response_data.encode('utf-8'))
        client.close()
        logger.debug("Закрываем соединение с клиентом")


def main():
    logger.debug("Запуск сервера")
    args = get_arguments()

    run_chat_server(args[0], args[1])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical(e)
