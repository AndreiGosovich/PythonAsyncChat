import argparse
import calendar
import dis
import inspect
import select
import threading
import time
from socket import *
import json
from datetime import datetime, timezone
import sys
import logging
from functools import wraps

from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer

from server_database import ServerDatabaseStorage
from gui_server import ServerWindow

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


# Дескриптор для описания порта:
class Port:
    def __set__(self, instance, value):
        if not 1023 < int(value) < 65536:
            error_string = f'Указан неверный порт {value}. Порт должен быть в диапазоне с 1024 до 65535.'
            logger.critical(error_string)
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


@log()
def get_arguments():
    logger.debug('Получаем аргументы')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='port', type=int, help='Port of server run. Default 7777')
    parser.add_argument('-a', dest='addr', type=str, help='PIP-address listen to. Default ALL')
    args = parser.parse_args()
    logger.debug(f'address = {args.addr}, port = {args.port}')
    return args.addr, args.port


class ServerVerifier(type):

    def __init__(self, clsname, bases, clsdict):
        for key, value in clsdict.items():

            # Проверка отсутствия объявления сокета на уровне класса
            if isinstance(value, socket):
                raise ValueError('Нельзя использовать Socket на уровне класса')

            # Проверка отсутствия connect для сокетов
            bad_methods = ['connect']
            if hasattr(value, "__call__"):  # Пропустить любые невызываемые объекты
                for instructions in dis.get_instructions(value):  # перебрать все инструкции
                    if instructions.opname == 'LOAD_METHOD' and instructions.argval in bad_methods:  # Проверить наличие вызова плохих методов
                        raise TypeError('Запрещено использовать методы accept и listen для сокетов')

            # Запретить использование других сокетов для работы, кроме TCP
            arg_vals = []
            if hasattr(value, "__call__"):  # Пропустить любые невызываемые объекты
                for instructions in dis.get_instructions(value):  # перебрать все инструкции
                    if instructions.opname == 'LOAD_GLOBAL':
                        arg_vals.append(instructions.argval)  # Собрать все все глобальные переменнные
                if ('AF_INET' in arg_vals or 'AF_INET6' in arg_vals) and 'SOCK_STREAM' not in arg_vals:  # Если используется TCP, то обязательно должно быть SOCK_STREAM
                    raise TypeError('Для сокетов необходимо использовать только TCP (SOCK_STREAM)')

        type.__init__(self, clsname, bases, clsdict)


class ServerClient(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, addr, port):
        self.addr = addr or ''
        self.port = port or 7777
        self.database = None  #
        self.server_is_active = False
        self.socket = None
        super().__init__()

    def set_database(self, connection_string, echo=False):
        self.database = ServerDatabaseStorage(connection_string, echo)

    # @log()
    def get_socket(self, addr, port):
        logger.debug("Создаём сокет")
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((addr, int(port)))
        s.listen(5)
        s.settimeout(0.2)  # Таймаут для операций с сокетом

        return s

    # @log()
    def parse_client_data(self, data):
        logger.debug("Парсим сообщение от клиента")
        client_data = json.loads(data)
        return client_data

    # @log()
    def get_response(self, client_data):
        logger.debug("Формируем ответ клиенту")
        action = client_data['action']

        code = 400
        alert = 'Неправильный запрос'

        message_to_send = {}

        if action == 'presence':
            print(type(client_data), client_data)
            # Проверить, что пользователь есть в списке, если нет - добавить
            if not self.database.get_user(client_data['user']['account_name']):
                user = self.database.add_user(client_data['user']['account_name'])
                code = 201
            else:
                code = 200
            alert = 'Ok'
        elif action == 'msg':
            code = 200
            alert = 'Ok'
            message_to_send = client_data
        elif action == 'get_contacts':
            code = 202
            alert = self.database.get_contacts(client_data['user_login'])
        elif action == 'add_contact':
            self.database.add_contact(client_data['user_id'], client_data['user_login'])
            code = 202
            alert = "Ok"
        elif action == 'del_contact':
            self.database.remove_contact(client_data['user_id'], client_data['user_login'])
            code = 202
            alert = "Ok"

        response = {
            "response": code,
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "alert": alert,
        }

        return (json.dumps(response) if len(message_to_send) == 0 else ''), message_to_send

    # @log()
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

    # @log()
    def send_messages(self, w_clients, all_clients, messages_to_send):
        """ Текстовое сообщение всем подключенным клиентам
        """
        for client in messages_to_send:
            # Сохранить в историю сообщений на сервере
            self.database.save_messge_to_history(messages_to_send[client]['from'],
                                                 messages_to_send[client]['to'],
                                                 messages_to_send[client]['message'])
            for sock in w_clients:
                try:
                    msg = json.dumps(messages_to_send[client])
                    sock.send(msg.encode('utf-8'))

                except TypeError as e:  # Сокет недоступен, клиент отключился
                    # logger.info('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
                    print(e)
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
            except Exception as e:
                print(e)
                logger.info('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
                all_clients.remove(sock)
        return responses, messages

    # @log()
    def run(self):
        clients = []
        messages_to_send = {}

        if not self.socket:
            self.socket = self.get_socket(self.addr, self.port)
        self.server_is_active = True

        logger.info("Сервер запущен")
        while self.server_is_active:
            try:
                client, addr = self.socket.accept()
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

    server_window_app = QtWidgets.QApplication(sys.argv)
    main_window = ServerWindow()

    server_client = ServerClient(main_window.edtAddress.text(), main_window.edtPort.text())
    server_client.set_database(main_window.edtConnectionString.text(), False)

    def connect():
        server_client.set_database(main_window.edtConnectionString.text(), False)
        server_client.addr = main_window.edtAddress.text()
        server_client.port = main_window.edtPort.text()
        if not server_client.server_is_active:
            server_client.daemon = True
            server_client.start()

        for _ in range(0, 30):
            if server_client.server_is_active:
                break
            time.sleep(0.5)

        if not server_client.server_is_active:
            raise ConnectionError('Не удалось выполнить подключение за указанное время.')

        main_window.database = server_client.database
        update_user_list()
        update_messages_history()

    main_window.btnConnect.clicked.connect(connect)

    def update_user_list():
        main_window.tblUsers.setModel(main_window.create_users_list_view())
        main_window.tblUsers.resizeColumnsToContents()
        main_window.tblUsers.resizeRowsToContents()
        # print(1)

    update_user_list()
    main_window.btnContacts.clicked.connect(update_user_list)

    def update_messages_history():
        main_window.lstMessages.setModel(main_window.create_messages_history_view(server_client.database, 20))

    update_messages_history()
    main_window.btnMessages.clicked.connect(update_messages_history)

    timer_update_user_list = QTimer()
    timer_update_user_list.timeout.connect(update_user_list)
    timer_update_user_list.start(1000)

    timer_update_messages_history = QTimer()
    timer_update_messages_history.timeout.connect(update_messages_history)
    timer_update_messages_history.start(1000)

    main_window.show()
    sys.exit(server_window_app.exec())


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical(e)
