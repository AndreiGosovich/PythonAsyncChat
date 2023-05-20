import calendar
import inspect
import json
import logging
import sys
import threading
import dis
from datetime import datetime, timezone
from socket import *
from functools import wraps
from select import select
from threading import Thread

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


class MessangerClient(metaclass=ClientVerifier):

    def __init__(self, user_name):
        self.user_name = user_name
        self.cv = threading.Condition()

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

    # @log
    def parse_server_response(self, data):
        logger.debug("Парсим ответ сервера")
        response_data = json.loads(data)

        if 'action' in response_data and response_data['action'] == 'msg' \
                and (response_data["to"] == self.user_name or response_data["to"].lower() == 'all'):
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

    # @log
    def sender(self, s):
        msg = self.create_presence_message('online')
        logger.debug("Отправляем Presense сообщение серверу")
        s.send(msg.encode('utf-8'))

        logger.debug('Чат запущен.')

        self.show_help()

        while True:
            msg = input('>')
            if msg == 'exit':
                break
            elif msg == 'help':
                self.show_help()
            else:
                try:
                    to_user, msg = msg.split(',')
                    msg = msg.strip()
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
        print('     <имя получателя>, <сообщение>: отправить сообщение указанному пользователю (ALL - всем)')

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

            logger.debug("Запускаем потоки...")
            receiver_thread = Thread(target=self.receiver, args=(s,))
            receiver_thread.daemon = True
            receiver_thread.start()

            sender_thread = Thread(target=self.sender, args=(s,))
            sender_thread.daemon = True
            sender_thread.start()

            sender_thread.join()


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
