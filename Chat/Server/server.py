import argparse
import calendar
from socket import *
import json
from datetime import datetime, timezone


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='port', type=int, help='Port of server run. Default 7777')
    parser.add_argument('-a', dest='addr', type=str, help='PIP-address listen to. Default ALL')
    args = parser.parse_args()
    return args.addr, args.port


def get_socket(addr, port):
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((addr, port))

    return s


def parse_client_data(data):
    client_data = json.loads(data)

    return client_data


def get_response(client_data):
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
    if not addr:
        addr = ''
    if not port:
        port = 7777

    s = get_socket(addr, port)
    s.listen(5)
    
    while True:
        client, addr = s.accept()
        data = client.recv(1000000).decode('utf-8')

        print(f'Получено сообщение:\n{data}\nот Клиента с адреса: {addr}')

        client_data = parse_client_data(data)

        response_data = get_response(client_data)

        client.send(response_data.encode('utf-8'))
        client.close()


def main():
    args = get_arguments()

    run_chat_server(args[0], args[1])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
