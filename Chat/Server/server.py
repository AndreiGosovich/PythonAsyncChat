import argparse
import calendar
import dis
import hashlib
import inspect
import select
# import socket
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
from gui_server import ServerWindow, AddUserDialogWindow

sys.path.append("..")
from log import server_log_config

logger = logging.getLogger('chat.server')


def log():
    """
    Декоратор для логирования запуска функций

    :return:
    """
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            logger.debug(f' Функция {func.__name__} вызвана из функции {inspect.stack()[1].function}')
            res = func(*args, **kwargs)
            return res
        return decorated
    return decorator


class Port:
    """
    Дескриптор для описания порта
    """
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
    """
    Парсинг параметров строки запуска

    :return: адрес, порт
    """
    logger.debug('Получаем аргументы')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='port', type=int, help='Port of server run. Default 7777')
    parser.add_argument('-a', dest='addr', type=str, help='PIP-address listen to. Default ALL')
    args = parser.parse_args()
    logger.debug(f'address = {args.addr}, port = {args.port}')
    return args.addr, args.port


@log()
def get_password_hash(password):
    """
    Генерация хэша пароля

    :param password: пароль (str)
    :return: хэш переданной строки (st
    """
    password = password.encode('utf-8')
    salt = 'Соль адыгейская, с пряностями'.encode('utf-8')
    password_hash = hashlib.pbkdf2_hmac('sha512', password, salt, 10000)
    return password_hash


def login_required(func):
    """
    Декоратор.
    Проверяется авторизован ли пользователь.
    Допускается обработка presence и authenticate сообщений, если пользователь не авторизован.

    :param func: проверяемая функция
    :return: проверяемая функция
    """
    def check_action(*args, **kwargs):
        check_result = False
        for client in args[0].active_users:
            if args[0].active_users[client] == args[2]:
                check_result = True

        if not check_result:
            data = args[1]
            if 'action' in data and data['action'] in ['presence', 'authenticate']:
                check_result = True

        if not check_result:
            raise ValueError("Пользователь не авторизован для данного действия")
        return func(*args, **kwargs)

    return check_action


class ServerVerifier(type):
    """Метакласс. Проверка использования отдельных методов и функций."""
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
    """Основной класс"""
    port = Port()
    """Переменная порта сервера"""

    def __init__(self, addr, port):
        """
        Инициализация экземпляра класса Сервера

        :param addr: адрес сервера
        :param port: порт сервера
        """
        self.addr = addr or ''
        self.port = port or 7777
        self.database = None  #
        self.server_is_active = False
        self.socket = None
        self.active_users = {}
        super().__init__()

    def set_database(self, connection_string, echo=False):
        """
        Настройка базы данных

        :param connection_string: строка подключения
        :param echo: вывод подробной информации о взаимодействии с БД
        :return: Не возвращает значений
        """
        self.database = ServerDatabaseStorage(connection_string, echo)

    def create_user(self, user_name, password, information=''):
        """
        Добавление в базу нового пользователя.

        :param user_name: Имя пользователя
        :param password: Пароль
        :param information: Информация о пользователе
        :return: Объект пользователя
        """
        password_hash = get_password_hash(password)
        return self.database.add_user(user_name, password_hash, information)

    def authenticate_user(self, user_name, password):
        """
        Проверка логина и пароля пользователя

        :param user_name: Имя пользователя
        :param password: Пароль
        :return: Результат проверки (boolean)
        """
        password_hash = get_password_hash(password)
        print(password, password_hash)
        if self.database.get_user_and_password(user_name, password_hash):
            return True
        return False

    # @log()
    def get_socket(self, addr, port):
        """
        Настройка сокета сервера

        :param addr: Адрес сервера
        :param port: Порт сервера
        :return: Объект сокета
        """
        logger.debug("Создаём сокет")
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((addr, int(port)))
        s.listen(5)
        s.settimeout(0.2)  # Таймаут для операций с сокетом

        return s

    # @log()
    def parse_client_data(self, data):
        """
        Конвертация сообщения клиента в словарь

        :param data: Текст сообщения в формате JSON
        :return: Словарь Python
        """
        logger.debug("Парсим сообщение от клиента")
        client_data = json.loads(data)
        return client_data

    # @log()
    @login_required
    def get_response(self, client_data, sock):
        """
        Подготовка ответа клиенту

        :param client_data: данные от клиента (dict)
        :param sock: экземпляр сокета клиента
        :return: (ответ сервера, пересылаемое сообщение)
        """
        logger.debug("Формируем ответ клиенту")
        action = client_data['action']

        code = 400
        alert = 'Неправильный запрос'

        message_to_send = {}

        if action == 'presence':
            print(type(client_data), client_data)
            # Проверить, что пользователь есть в списке, если нет - добавить
            if not self.database.get_user(client_data['user']['account_name']):
                # user = self.database.add_user(client_data['user']['account_name'])
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
        elif action == 'authenticate':
            user_name = client_data['user']['account_name']
            if self.authenticate_user(user_name, client_data['user']['password']):
                code = 200
                self.active_users[user_name] = sock
                print(type(sock), sock)
            else:
                self.active_users.pop(user_name, None)
                code = 402
                alert = "Пользователь не авторизован"

        response = {
            "response": code,
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "alert": alert,
        }

        return (json.dumps(response) if len(message_to_send) == 0 else ''), message_to_send

    # @log()
    def write_responses(self, requests, w_clients, all_clients):
        """
        Отправка ответов сервера

        :param requests: запросы (dict)
        :param w_clients: список клиентов на чтение
        :param all_clients: список всех подключенных клиентов
        :return: не возвращает значений
        """
        for sock in w_clients:
            if sock in requests:
                try:
                    # Подготовить и отправить ответ сервера
                    resp = requests[sock]
                    sock.send(resp.encode('utf-8'))
                except:  # Сокет недоступен, клиент отключился
                    logger.info('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
                    self.remove_from_active(sock)
                    sock.close()
                    all_clients.remove(sock)

    # @log()
    def send_messages(self, w_clients, all_clients, messages_to_send):
        """
        Отправка сообщений клиентам

        :param w_clients: ожидающие клиенты
        :param all_clients: все подключенные клиенты
        :param messages_to_send: сообщение для отправки
        :return: не возвращает значений
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
                    self.remove_from_active(sock)
                    print(e)
                    sock.close()
                    all_clients.remove(sock)

    # @log()
    def read_requests(self, r_clients, all_clients):
        """
        Чтение запросов из списка клиентов

        :param r_clients: Список клиентов, которые что-то прислали
        :param all_clients: Список всех клиентов
        :return: не возвращает значений
        """
        responses = {}  # Словарь ответов сервера вида {сокет: запрос}
        messages = {}  # Словарь сообщений
        for sock in r_clients:
            try:
                data = self.parse_client_data(sock.recv(1024).decode('utf-8'))
                responses[sock], message = self.get_response(data, sock)
                if len(message):
                    messages[sock] = message
                logger.info(f'Получено сообщение: {data} от Клиента: {sock.fileno()} {sock.getpeername()}')
            except Exception as e:
                print(e)
                self.remove_from_active(sock)
                logger.info('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
                all_clients.remove(sock)
        return responses, messages

    def remove_from_active(self, sock):
        """
        Удалить клиента из активных

        :param sock: Сокет отключенного клиента
        :return: не возвращает значений
        """
        for user in self.active_users.copy():
            if self.active_users[user] == sock:
                self.active_users.pop(user, None)

    # @log()
    def run(self):
        """
        Основной метод класса. Запускает поток сервера.

        :return: Не возвращает значений
        """
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
    """Создание экземпляра класса, создание интерфейса, запуск клиента"""
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

    def add_user_window():
        if server_client.server_is_active:
            def add_user(user_name, password, information):
                if user_name and password:
                    server_client.create_user(user_name, password, information)
                    update_user_list()

            dialog = AddUserDialogWindow(main_window)
            dialog.accepted.connect(lambda: add_user(dialog.edtLogin.text(),
                                                     dialog.edtPassword.text(),
                                                     dialog.textEdit.toPlainText()
                                                     )
                                    )
            dialog.open()

    main_window.btnAddUser.clicked.connect(add_user_window)

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
