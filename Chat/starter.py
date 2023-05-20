import platform
import subprocess


def run_chat_subprocess(user_name, addr='localhost', port=7777):
    return subprocess.Popen(['python3', 'client.py', addr, str(port), user_name],
                            cwd='../Chat/Client/',
                            creationflags=0 if not platform.system().lower() == 'windows' else subprocess.CREATE_NEW_CONSOLE,
                            shell=False,
                            )


def run_many_chats(count_chats=1, addr='localhost', port=7777):
    chat_clients = []
    for i in range(1, count_chats + 1):
        chat_clients.append(run_chat_subprocess(f'User{i}', addr, port))
    return chat_clients


def start_server(addr='localhost', port=7777):
    return subprocess.Popen(['python3', 'server.py', '-p', str(port), '-a', addr],
                            cwd='./Server/',
                            creationflags=0 if not platform.system().lower() == 'windows' else subprocess.CREATE_NEW_CONSOLE,
                            shell=False,
                            )


def main():
    subprocesses = []
    while True:
        action = input('Выберите действие: \n'
                       '    server - старт сервера\n'
                       '    client - запуск обычного клиента чата\n'
                       '    test - старт тестовых клиентов\n'
                       '    kill - закрыть все процессы\n'
                       '    exit - выход \n'
                       '> ')
        if action == 'server':
            addr = input('адрес (пусто = localhost): ')
            port = input('порт (пусто = 7777): ')
            subprocesses.append(start_server('localhost' if not addr else addr, 7777 if not port else int(port)))
        elif action == 'client':
            username = input('Пользователь: ')
            addr = input('адрес (пусто = localhost): ')
            port = input('порт (пусто = 7777): ')
            subprocesses.append(run_chat_subprocess(username, addr, 7777 if not port else int(port)))
        elif action == 'test':
            count_chats = input('Количество (пусто = 1): ')
            addr = input('адрес (пусто = localhost): ')
            port = input('порт (пусто = 7777): ')
            for p in run_many_chats(1 if not count_chats else int(count_chats), addr, 7777 if not port else int(port)):
                subprocesses.append(p)
        elif action == 'kill':
            while subprocesses:
                subprocesses.pop().kill()
        elif action == 'exit':
            while subprocesses:
                subprocesses.pop().kill()
            break


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
