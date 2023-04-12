import json
import sys
from socket import *
from datetime import datetime, timezone


def get_arguments():
    args = sys.argv
    if len(args) > 1:
        addr = args[1]
    else:
        print('Invalid address')
        exit(1)

    port = 0
    if len(args) > 2:
        port = int(args[2])

    return addr, port


def create_presence_message(account_name, status='online', _type='status'):
    return json.dumps({
        "action": "presence",
        "time":  datetime.now(timezone.utc).timestamp() * 1000,
        "type": _type,
        "user": {
            "account_name": account_name,
            "status": status,
        }
    })


def parse_server_response(data):
    response_data = json.loads(data)

    return response_data


def run_chat_client(addr='', port=7777):
    if not addr:
        addr = ''
    if not port:
        port = 7777

    s = socket(AF_INET, SOCK_STREAM)  # Создать сокет TCP
    s.connect((addr, port))  # Соединиться с сервером

    msg = create_presence_message('presence')

    s.send(msg.encode('utf-8'))
    data = s.recv(1000000)

    server_response = parse_server_response(data.decode('utf-8'))

    print('Сообщение от сервера: ', server_response, ', длиной ', len(data), ' байт')
    s.close()


def main():
    args = get_arguments()

    run_chat_client(args[0], args[1])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
