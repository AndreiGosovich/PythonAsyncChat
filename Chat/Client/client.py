import calendar
import inspect
import json
import logging
import os
import sys
import threading
import dis
import time
from datetime import datetime, timezone
from socket import socket, AF_INET, SOCK_STREAM
from functools import wraps
from threading import Thread
from PyQt6 import QtWidgets

path = os.path.abspath(os.path.join(".."))
sys.path.append(path)

from client_database import ClientDatabaseStorage
from gui_client import ClientWindow, ChatDialogWindow, AddContactDialogWindow,\
    DelContactDialogWindow
import client_log_config

logger = logging.getLogger('chat.client')


def log(func):
    """
    Декоратор. Логгер срабатывания функции

    :param func: Оборачиваемая функция
    :return: Оборачиваемая функция
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        logger.debug(f' Функция {func.__name__} вызвана из функции '
                     f'{inspect.stack()[1].function}')
        res = func(*args, **kwargs)
        return res

    return decorated


@log
def get_arguments():
    """
    Парсер строки запуска

    :return: адрес, порт, имя пользователя
    """
    logger.debug('Получаем аргументы')
    args = sys.argv
    if len(args) > 1:
        addr = args[1]
    else:
        # raise SystemExit('Invalid address')
        addr = ""

    port = 0
    if len(args) > 2:
        port = int(args[2])

    user_name = ''
    if len(args) > 3:
        user_name = args[3]

    logger.info(f'address = {addr}, port = {port}, user_name = {user_name}')
    return addr, port, user_name


class ClientVerifier(type):
    """Метакласс проверки корректности использования отдельных методов"""
    def __init__(self, clsname, bases, clsdict):
        for key, value in clsdict.items():

            # Проверка отсутствия объявления сокета на уровне класса
            if isinstance(value, socket):
                raise ValueError('Нельзя использовать Socket на уровне класса')

            # Проверка отсутствия accept и listen для сокетов
            bad_methods = ['accept', 'listen']
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


class MessangerClient(Thread, metaclass=ClientVerifier):
    """Основной класс проекта"""
    def __init__(self, user_name, password, addr='localhost', port=7777):
        """
        Экземпляр класса клиента чата

        :param user_name: Имя пользователя
        :param password: Пароль
        :param addr: Адрес сервера
        :param port: Порт на сервере
        """
        self.user_name = user_name
        self.password = password
        self.addr = addr
        self.port = port
        self.socket = None  # self.get_socket(AF_INET, SOCK_STREAM)
        self.cv = threading.Condition()
        self.database = ClientDatabaseStorage('sqlite:///client_database.sqlite3', False)
        self.lock = threading.Lock()
        self.client_is_active = False
        self.is_authenticate = False
        super().__init__()

    # @log
    def create_presence_message(self, status='online', _type='status'):
        """
        Создание presence сообщения

        :param status: Статус подключения
        :param _type: тип сообщения
        :return: Сообщение в формате JSON
        """
        logger.debug("Создаём presence сообщение серверу")
        return json.dumps({
            "action": "presence",
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "type": _type,
            "user": {
                "account_name": self.user_name,
                "status": status,
            }
        })

    def create_authenticate_message(self):
        """
        Создание сообщения аутентификации

        :return: Сообщение в формате JSON
        """
        logger.debug("Создаём authenticate сообщение серверу")

        return json.dumps({
            "action": "authenticate",
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "user": {
                "account_name": self.user_name,
                "password": self.password,
            }
        })

    # @log
    def create_text_message(self, to_user, message, encoding='utf-8'):
        """
        Создание сообщения другому пользователю

        :param to_user: Кому отправить
        :param message: Текст сообщения
        :param encoding: Кодировка
        :return: Сообщение в формате JSON
        """
        logger.debug("Создаём текстовое сообщение")
        return json.dumps({
            "action": "msg",
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "to": to_user,
            "from": self.user_name,
            "encoding": encoding,
            "message": message,
        })

    def create_get_contacts_message(self):
        """
        Создание сообщения запроса списка контактов пользователя

        :return: Сообщение в формате JSON
        """
        logger.debug("Создаём запрос списка контактов пользователя")
        return json.dumps({
            "action": "get_contacts",
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "user_login": self.user_name,
        })

    def create_add_contacts_message(self, contact):
        """
        Создание сообщения добавления контакта в список контактов пользователя

        :param contact: Имя пользователя - контакта
        :return: Сообщение в формате JSON
        """
        logger.debug("Создаём запрос на добавление контакта в список")
        return json.dumps({
            "action": "add_contact",
            "user_id": self.user_name,
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "user_login": contact,
        })

    def create_del_contacts_message(self, contact):
        """
        Создание сообщения удаления контакта из списка контактов пользователя

        :param contact: Имя пользователя - контакта
        :return: Сообщение в формате JSON
        """
        logger.debug("Создаём запрос на добавление контакта в список")
        return json.dumps({
            "action": "del_contact",
            "user_id": self.user_name,
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "user_login": contact,
        })

    # @log
    def parse_server_response(self, data):
        """
        Обработка сообщения от сервера

        :param data: сырое сообщения
        :return: Сообщение в формате dict
        """
        logger.debug("Парсим ответ сервера")
        response_data = json.loads(data)

        if 'action' in response_data and response_data['action'] == 'msg' \
                and (response_data["to"] == self.user_name or response_data["to"].lower() == 'all'):
            self.database.save_message_to_history(response_data["from"], response_data["to"], response_data["message"])
            response_data = f'{response_data["from"]}: {response_data["message"]}'
            return response_data
        return False

    # @log
    def get_socket(self, addr_family, socket_type):
        """
        Создание сокета подключения к серверу

        :param addr_family: Тип адреса
        :param socket_type: Тип сокета
        :return: Объект сокета
        """
        logger.debug("Создаём сокет")
        s = socket(addr_family, socket_type)  # Создать сокет TCP
        s.connect((self.addr, self.port))  # Соединиться с сервером
        s.settimeout(1)

        return s

    # @log
    def receiver(self):
        """Приём сообщений от сервера"""
        while self.client_is_active:
            time.sleep(1)
            with self.lock:
                try:
                    data = self.socket.recv(1000000).decode('utf-8')

                    if data:
                        logger.debug(f'Сообщение от сервера: {data}, длиной {len(data)} байт')
                        server_response = self.parse_server_response(data)
                        if server_response:
                            print(f'\n{server_response}\n>', end='')
                    else:
                        logger.critical("Server close connection")
                        self.socket.close()
                        break
                except OSError as err:
                    if err.errno:
                        logger.critical('Lost server connection')
                        self.socket.close()
                        break

    def send_message(self, to_user, msg):
        """
        Отправка сообщения

        :param to_user: КОму отправить
        :param msg: Текст сообщения
        """
        msg = msg.strip()
        with self.lock:
            self.database.save_message_to_history(self.user_name, to_user, msg)
            msg = self.create_text_message(to_user, msg)
            self.socket.send(msg.encode('utf-8'))  # Отправить!

    # @log
    def sender(self):
        """Отправка сообщений серверу"""
        logger.debug('Чат запущен.')

        self.show_help()

        while self.client_is_active:
            msg = input('>')
            if msg == 'exit':
                # break
                self.client_is_active = False
            elif msg == 'help':
                self.show_help()
            elif msg == 'contacts':
                self.contacts_manager()
            elif msg == 'm':
                self.show_messages_history(self.user_name, input('Введите ник пользователя: '))
            else:
                to_user, msg = msg.split(',')
                try:
                    self.send_message(to_user, msg)
                except OSError:
                    logger.critical('Соединение с сервером разорвано. Перезапустите клиент.')
                    self.socket.close()
                    break
                except ValueError:
                    print('Неправильный формат сообщения!')
                    self.show_help()

    # @log
    # def ask_user_name(self):
    #     user_name = ''
    #     while not user_name:
    #         user_name = input('Укажите имя пользователя: ')
    #     self.user_name = user_name

    # @log
    def show_help(self):
        """Отображение подсказки в консоли"""
        print('Команды в чате:')
        print('     help: показать эту подсказку')
        print('     exit: закрыть клиент')
        print('     contacts: работа с контактами')
        print('     m: историю сообщений с контактом')
        print('     <имя получателя>, <сообщение>: отправить сообщение указанному пользователю (ALL - всем)')

    def send_presense(self, status):
        """
        Отправка presense сообщения

        :param status:статус пользователя
        """
        msg = self.create_presence_message(status)
        logger.debug("Отправляем Presense сообщение серверу")

        with self.lock:
            self.socket.send(msg.encode('utf-8'))
            data = self.socket.recv(1000000).decode('utf-8')

        if data:
            logger.debug(f'Сообщение от сервера: {data}, длиной {len(data)} байт')

    def contacts_manager(self):
        """Обработка меню контактов в консоли"""
        print('Выберите действие')
        print('     list:   вывести список контактов')
        print('     add:    добавить контакт')
        print('     del: удалить контакт')
        action = input('>')
        if action == 'list':
            self.show_contacts()
        elif action == 'add':
            self.add_or_del_contact(self.socket, input('Введите ник пользователя: '), action)
        elif action == 'del':
            self.add_or_del_contact(self.socket, input('Введите ник пользователя: '), action)

    def get_contacts(self):
        """Запрос списка контаков"""
        msg = self.create_get_contacts_message()
        logger.debug("Отправляем Запрос списка контактов")

        with self.lock:
            self.socket.send(msg.encode('utf-8'))
            data = self.socket.recv(1000000).decode('utf-8')

            if data:
                logger.debug(f'Сообщение от сервера: {data}, длиной {len(data)} байт')
                server_response = json.loads(data)
                if server_response and 'alert' in server_response and len(server_response['alert']):
                    self.database.remove_all_contacts()
                    for contact in server_response['alert']:
                        self.database.add_contact(self.user_name, contact)

    def show_contacts(self):
        """Отображение списка контактов в консоли"""
        contact_list = self.database.get_contacts(self.user_name)
        for c in contact_list:
            print(c)

    def add_or_del_contact(self, contact, action):
        """
        Добавление или удаление контакта в список

        :param contact: Контакт
        :param action: Дабваить или удалить
        """
        if action == 'add':
            msg = self.create_add_contacts_message(contact)
            logger.debug("Отправляем Запрос добавления контакта")
        elif action == 'del':
            msg = self.create_del_contacts_message(contact)
            logger.debug("Отправляем Запрос удаления контакта")
        else:
            return

        with self.lock:
            self.socket.send(msg.encode('utf-8'))

            data = self.socket.recv(1000000).decode('utf-8')

            if data:
                logger.debug(f'Сообщение от сервера: {data}, длиной {len(data)} байт')
                server_response = json.loads(data)
        if server_response and server_response['response'] and server_response['response'] in range(200, 300):
            self.get_contacts()

    def show_messages_history(self, user_from, user_to):
        """
        Отображение истории сообщений с пользователем в консоли

        :param user_from: Пользователь от кого
        :param user_to: Пользователь кому
        """
        messages = self.database.get_message_history(user_from, user_to)
        for m in messages:
            print(f'({m[3]}) {m[0]}: {m[2]}')

    def authenticate(self):
        """Аутентификация пользователя на сервере. True, если авторизация успешна."""
        msg = self.create_authenticate_message()
        logger.debug("Отправляем Запрос аутентификации")

        with self.lock:
            self.socket.send(msg.encode('utf-8'))
            data = self.socket.recv(1000000).decode('utf-8')

            if data:
                logger.debug(f'Сообщение от сервера: {data}, длиной {len(data)} байт')
                server_response = json.loads(data)
                if server_response and 'response' in server_response and server_response and 'alert' in server_response:
                    if server_response['response'] == 200:
                        return True
                    logger.critical(f'Ошибка авторизации на сервере. '
                                    f'Код {server_response["response"]}, описание: {server_response["alert"]}')
        return False

    # @log
    def run(self):
        """Основной метод класса. Запуск логики."""
        logger.debug("Подключаемся...")

        if not self.socket:
            self.socket = self.get_socket(AF_INET, SOCK_STREAM)

        self.client_is_active = True

        logger.debug("Запускаем потоки...")
        receiver_thread = Thread(target=self.receiver)
        receiver_thread.daemon = True
        receiver_thread.start()

        sender_thread = Thread(target=self.sender)
        sender_thread.daemon = True
        sender_thread.start()
        # sender_thread.join()
        #
        while self.client_is_active:
            if not receiver_thread.is_alive() or not sender_thread.is_alive():
                break
            time.sleep(1)


def ask_user_name():
    """
    Запрос имени пользователя в консоли

    :return: Имя пользователя
    """
    user_name = ''
    while not user_name:
        user_name = input('Укажите имя пользователя: ')
    return user_name


@log
def main():
    """Порядок запуска и настройки логики работы приложения"""
    logger.debug("Запускаем клиент чата")
    print("Запускаем клиент чата")
    args = get_arguments()
    user_nane = args[2]

    client_window_app = QtWidgets.QApplication(sys.argv)
    main_window = ClientWindow()
    client = MessangerClient(main_window.edtUserName.text(), main_window.adtPassword.text())

    def connect():
        client.user_name = main_window.edtUserName.text()
        client.password = main_window.adtPassword.text()
        if not client.client_is_active:
            client.daemon = True
            client.start()

        for _ in range(0, 30):
            if client.client_is_active:
                break
            time.sleep(0.5)

        if not client.client_is_active:
            raise ConnectionError('Не удалось выполнить подключение за указанное время.')

        # client.send_presense('online')
        if client.authenticate():
            client.is_authenticate = True
            main_window.database = client.database
            main_window.username = main_window.edtUserName.text()
            main_window.addr = main_window.edtAddres.text()
            main_window.port = main_window.edtPort.text()
            update_contact_list()
        else:
            main_window.lstContacts.setModel(main_window.set_error('Ошибка подключения к серверу'))

    main_window.btnConnect.clicked.connect(connect)

    def update_contact_list():
        if client.client_is_active and client.is_authenticate:
            client.get_contacts()
            main_window.lstContacts.setModel(main_window.get_contacts_view())

    update_contact_list()

    def messages_window():
        user_to = main_window.lstContacts.currentIndex().data()
        if user_to:
            dialog = ChatDialogWindow(user_to, main_window)

            def update_messages():
                dialog.lstMessges.setModel(dialog.create_messages_history_view(user_to))

            update_messages()

            def send_message_btn_action():
                if dialog.txtMessage.toPlainText():
                    client.send_message(user_to, dialog.txtMessage.toPlainText())
                    dialog.txtMessage.clear()
                    update_messages()

            dialog.btnSend.clicked.connect(send_message_btn_action)
            dialog.btnRefresh.clicked.connect(update_messages)

            dialog.open()

    main_window.lstContacts.doubleClicked.connect(messages_window)

    def add_contact_window():
        def add_contact(contact):
            if contact:
                client.add_or_del_contact(contact, 'add')
                update_contact_list()

        dialog = AddContactDialogWindow(main_window)
        dialog.accepted.connect(lambda: add_contact(dialog.edtUserName.text()))
        dialog.open()

    main_window.btnAddContact.clicked.connect(add_contact_window)

    def dell_contact_window():
        contact = main_window.lstContacts.currentIndex().data()
        def del_contact(contact):
            if contact:
                client.add_or_del_contact(contact, 'del')
                update_contact_list()

        dialog = DelContactDialogWindow(contact, main_window)
        dialog.accepted.connect(lambda: del_contact(dialog.edtUserName.toPlainText()))
        dialog.open()

    main_window.btnDelContact.clicked.connect(dell_contact_window)

    main_window.show()
    sys.exit(client_window_app.exec())


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical(e)
