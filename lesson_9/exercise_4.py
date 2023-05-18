# 4. Продолжаем работать над проектом «Мессенджер»:
# a) Реализовать скрипт, запускающий два клиентских приложения: на чтение чата и на запись в него.
#   Уместно использовать модуль subprocess).
# b) Реализовать скрипт, запускающий указанное количество клиентских приложений.

import subprocess


def run_chat_subprocess(user_name, mode='read'):
    if mode == 'write':
        p = subprocess.run(['python3', 'client.py', 'localhost', '7777', user_name], cwd='../Chat/Client/')
    else:
        p = subprocess.Popen(['python3', 'client.py', 'localhost', '7777', user_name], cwd='../Chat/Client/',
                             stdout=subprocess.PIPE,
                             shell=False)
    return p


def run_many_chats(count_chats=1, mode='read'):
    chat_clients = list()
    for i in range(1, count_chats + 1):
        chat_clients.append(run_chat_subprocess(f'User{i}', mode))

    while True:
        for i in range(len(chat_clients) - 1):
            if chat_clients[i].poll():
                del chat_clients[i]
        if not len(chat_clients):
            break


if __name__ == '__main__':
    try:
        run_many_chats(5, 'read')
        run_chat_subprocess('User0', 'write')
    except Exception as e:
        print(e)
