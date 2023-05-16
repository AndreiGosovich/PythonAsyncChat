import argparse
import calendar
import inspect
import select
from socket import *
import json
from datetime import datetime, timezone
import sys
import logging
from functools import wraps

sys.path.append("..")
from log import server_log_config

logger = logging.getLogger('chat.server')


def log():
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            logger.debug(f' Функция {func.__name__} вызвана из функции {inspect.stack()[1].function}')
            res = func(*args, **kwargs)
            return res
        return decorated
    return decorator


@log()
def get_arguments():
    logger.debug('Получаем аргументы')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='port', type=int, help='Port of server run. Default 7777')
    parser.add_argument('-a', dest='addr', type=str, help='PIP-address listen to. Default ALL')
    args = parser.parse_args()
    logger.debug(f'address = {args.addr}, port = {args.port}')
    return args.addr, args.port


class ServerClient:
    @log()
    def get_socket(self, addr, port):
        logger.debug("Создаём сокет")
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((addr, port))
        s.listen(5)
        s.settimeout(0.2)  # Таймаут для операций с сокетом

        return s

    @log()
    def parse_client_data(self, data):
        logger.debug("Парсим сообщение от клиента")
        client_data = json.loads(data)

        return client_data

    @log()
    def get_response(self, client_data):
        logger.debug("Формируем ответ клиенту")
        action = client_data['action']

        code = 400
        alert = 'Неправильный запрос'

        message_to_send = {}

        if action == 'presence':
            code = 200
            alert = 'Ok'
        elif action == 'msg':
            code = 200
            alert = 'Ok'
            message_to_send = client_data

        response = {
            "response": code,
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "alert": alert,
        }
        return json.dumps(response), message_to_send

    @log()
    def write_responses(self, requests, w_clients, all_clients):
        """ Эхо-ответ сервера клиентам, от которых были запросы
        """
        for sock in w_clients:
            if sock in requests:
                try:
                    # Подготовить и отправить ответ сервера
                    resp = requests[sock]
                    sock.send(resp.encode('utf-8'))
                except:  # Сокет недоступен, клиент отключился
                    logger.info('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
                    sock.close()
                    all_clients.remove(sock)

    @log()
    def send_messages(self, w_clients, all_clients, messages_to_send):
        """ Текстовое сообщение всем подключенным клиентам
        """
        for client in messages_to_send:
            for sock in w_clients:
                try:
                    msg = json.dumps(messages_to_send[client])
                    sock.send(msg.encode('utf-8'))
                except:  # Сокет недоступен, клиент отключился
                    # logger.info('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
                    sock.close()
                    all_clients.remove(sock)

    # @log()
    def read_requests(self, r_clients, all_clients):
        """ Чтение запросов из списка клиентов
        """
        responses = {}  # Словарь ответов сервера вида {сокет: запрос}
        messages = {}  # Словарь сообщений
        for sock in r_clients:
            try:
                data = self.parse_client_data(sock.recv(1024).decode('utf-8'))
                responses[sock], message = self.get_response(data)
                if len(message):
                    messages[sock] = message
                logger.info(f'Получено сообщение: {data} от Клиента: {sock.fileno()} {sock.getpeername()}')
            except:
                logger.info('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
                all_clients.remove(sock)
        return responses, messages

    @log()
    def run_chat_server(self, addr='', port=7777):
        # logger.info("Запускаем сервер")
        if not addr:
            addr = ''
        if not port:
            port = 7777

        clients = []
        messages_to_send = {}

        s = self.get_socket(addr, port)
        logger.info("Сервер запущен")
        while True:
            try:
                client, addr = s.accept()
            except OSError as e:
                pass  # timeout вышел
            else:
                logger.info("Получен запрос на соединение от %s" % str(addr))
                clients.append(client)
            finally:
                # Проверить наличие событий ввода-вывода
                wait = 1
                r = []
                w = []

                try:
                    r, w, e = select.select(clients, clients, [], wait)
                except:
                    pass  # Ничего не делать, если какой-то клиент отключился

                requests, messages_to_send = self.read_requests(r, clients)  # Сохраним запросы клиентов
                if requests:
                    self.write_responses(requests, w, clients)  # Выполним отправку ответов клиентам

                if len(messages_to_send) and w:
                    self.send_messages(w, clients, messages_to_send)
                    messages_to_send.clear()


@log()
def main():
    logger.info("Запуск сервера")
    args = get_arguments()

    server_client = ServerClient()
    server_client.run_chat_server(args[0], args[1])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical(e)
