import calendar
import inspect
import json
import logging
import socket
import sys
import threading
import dis
import time
from datetime import datetime, timezone
from socket import *
from functools import wraps
from select import select
from threading import Thread, Lock
from client_database import ClientDatabaseStorage

sys.path.append("..")
from log import client_log_config

logger = logging.getLogger('chat.client')


def log(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        logger.debug(f' Функция {func.__name__} вызвана из функции {inspect.stack()[1].function}')
        res = func(*args, **kwargs)
        return res

    return decorated


@log
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

    user_name = ''
    if len(args) > 3:
        user_name = args[3]

    logger.info(f'address = {addr}, port = {port}, user_name = {user_name}')
    return addr, port, user_name


class ClientVerifier(type):

    def __init__(self, clsname, bases, clsdict):
        for key, value in clsdict.items():
            # print(key, value)

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

    def __init__(self, user_name):
        self.user_name = user_name
        self.cv = threading.Condition()
        self.database = ClientDatabaseStorage('sqlite:///client_database.sqlite3', False)
        self.lock = threading.Lock()
        super().__init__()

    # @log
    def create_presence_message(self, status='online', _type='status'):
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

    # @log
    def create_text_message(self, to_user, message, encoding='utf-8'):
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
        logger.debug("Создаём запрос списка контактов пользователя")
        return json.dumps({
            "action": "get_contacts",
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "user_login": self.user_name,
        })

    def create_add_contacts_message(self, contact):
        logger.debug("Создаём запрос на добавление контакта в список")
        return json.dumps({
            "action": "add_contact",
            "user_id": self.user_name,
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "user_login": contact,
        })

    def create_del_contacts_message(self, contact):
        logger.debug("Создаём запрос на добавление контакта в список")
        return json.dumps({
            "action": "del_contact",
            "user_id": self.user_name,
            "time": calendar.timegm(datetime.now(timezone.utc).utctimetuple()),
            "user_login": contact,
        })

    # @log
    def parse_server_response(self, data):
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
        logger.debug("Создаём сокет")
        s = socket(addr_family, socket_type)  # Создать сокет TCP

        return s

    # @log
    def receiver(self, s):
        while True:
            time.sleep(1)
            with self.lock:
                try:
                    data = s.recv(1000000).decode('utf-8')

                    if data:
                        logger.debug(f'Сообщение от сервера: {data}, длиной {len(data)} байт')
                        server_response = self.parse_server_response(data)
                        if server_response:
                            print(f'\n{server_response}\n>', end='')
                    else:
                        logger.critical("Server close connection")
                        s.close()
                        break
                except OSError as err:
                    if err.errno:
                        logger.critical('Lost server connection')
                        s.close()
                        break

    # @log
    def sender(self, s):
        logger.debug('Чат запущен.')

        self.show_help()

        while True:
            msg = input('>')
            if msg == 'exit':
                break
            elif msg == 'help':
                self.show_help()
            elif msg == 'contacts':
                self.contacts_manager(s)
            elif msg == 'm':
                self.show_messages_history(self.user_name, input('Введите ник пользователя: '))
            else:
                with self.lock:
                    try:
                        to_user, msg = msg.split(',')
                        msg = msg.strip()
                        self.database.save_message_to_history(self.user_name, to_user, msg)
                        msg = self.create_text_message(to_user, msg)
                        s.send(msg.encode('utf-8'))  # Отправить!
                    except OSError:
                        logger.critical('Соединение с сервером разорвано. Перезапустите клиент.')
                        s.close()
                        break
                    except ValueError:
                        print('Неправильный формат сообщения!')
                        self.show_help()

    # @log
    def ask_user_name(self):
        user_name = ''
        while not user_name:
            user_name = input('Укажите имя пользователя: ')
        self.user_name = user_name

    # @log
    def show_help(self):
        print('Команды в чате:')
        print('     help: показать эту подсказку')
        print('     exit: закрыть клиент')
        print('     contacts: работа с контактами')
        print('     m: историю сообщений с контактом')
        print('     <имя получателя>, <сообщение>: отправить сообщение указанному пользователю (ALL - всем)')

    def send_presense(self, s, status):
        msg = self.create_presence_message(status)
        logger.debug("Отправляем Presense сообщение серверу")

        with self.lock:
            s.send(msg.encode('utf-8'))
            data = s.recv(1000000).decode('utf-8')

        if data:
            logger.debug(f'Сообщение от сервера: {data}, длиной {len(data)} байт')

    def contacts_manager(self, s):
        print('Выберите действие')
        print('     list:   вывести список контактов')
        print('     add:    добавить контакт')
        print('     del: удалить контакт')
        action = input('>')
        if action == 'list':
            self.show_contacts(s)
        elif action == 'add':
            self.add_or_del_contact(s, input('Введите ник пользователя: '), action)
        elif action == 'del':
            self.add_or_del_contact(s, input('Введите ник пользователя: '), action)

    def get_contacts(self, s):
        msg = self.create_get_contacts_message()
        logger.debug("Отправляем Запрос списка контактов")

        with self.lock:
            s.send(msg.encode('utf-8'))
            data = s.recv(1000000).decode('utf-8')

            if data:
                logger.debug(f'Сообщение от сервера: {data}, длиной {len(data)} байт')
                server_response = json.loads(data)
                if server_response and 'alert' in server_response and len(server_response['alert']):
                    self.database.remove_all_contacts()
                    for contact in server_response['alert']:
                        self.database.add_contact(self.user_name, contact)

    def show_contacts(self, s):
        contact_list = self.database.get_contacts(self.user_name)
        for c in contact_list:
            print(c)

    def add_or_del_contact(self, s, contact, action):
        if action == 'add':
            msg = self.create_add_contacts_message(contact)
            logger.debug("Отправляем Запрос добавления контакта")
        elif action == 'del':
            msg = self.create_del_contacts_message(contact)
            logger.debug("Отправляем Запрос удаления контакта")
        else:
            return

        with self.lock:
            s.send(msg.encode('utf-8'))

            data = s.recv(1000000).decode('utf-8')

            if data:
                logger.debug(f'Сообщение от сервера: {data}, длиной {len(data)} байт')
                server_response = json.loads(data)
        if server_response and server_response['response'] and server_response['response'] in range(200, 300):
            self.get_contacts(s)

    def show_messages_history(self, user_from, user_to):
        messages = self.database.get_message_history(user_from, user_to)
        #     [m.user_from, m.user_to, m.message, m.time_send]
        for m in messages:
            print(f'({m[3]}) {m[0]}: {m[2]}')

    # @log
    def run_chat_client(self, addr='', port=7777):
        logger.debug("Подключаемся...")
        if not addr:
            addr = ''
        if not port:
            port = 7777

        if not self.user_name:
            self.ask_user_name()

        with self.get_socket(AF_INET, SOCK_STREAM) as s:
            s.connect((addr, port))  # Соединиться с сервером

            s.settimeout(1)

            self.send_presense(s, 'online')
            self.get_contacts(s)  # Получить список контактов

            logger.debug("Запускаем потоки...")
            receiver_thread = Thread(target=self.receiver, args=(s,))
            receiver_thread.daemon = True
            receiver_thread.start()

            sender_thread = Thread(target=self.sender, args=(s,))
            sender_thread.daemon = True
            sender_thread.start()
            # sender_thread.join()
            #
            while True:
                if not receiver_thread.is_alive() or not sender_thread.is_alive():
                    break
                time.sleep(5)

@log
def main():
    logger.debug("Запускаем клиент чата")
    print("Запускаем клиент чата")
    args = get_arguments()

    client = MessangerClient(args[2])
    client.run_chat_client(args[0], args[1])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical(e)
