import argparse
from socket import *
import json
from datetime import datetime, timezone


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='port', type=int, help='Port of server run. Default 7777')
    parser.add_argument('-a', dest='addr', type=str, help='PIP-address listen to. Default ALL')
    args = parser.parse_args()
    return args


def get_response(code, alert):
    response = {
            "response": code,
            "time": datetime.now(timezone.utc).timestamp() * 1000,
            "alert": alert,
        }

    return json.dumps(response)


def parse_client_data(data):
    response_data = json.loads(data)
    action = response_data['action']

    if action == 'presence':
        response_data = get_response(200, 'Ok')
        return response_data

    return get_response(400, 'Invalid Action')


def run_chat_server(addr='', port=7777):
    if not addr:
        addr = ''
    if not port:
        port = 7777

    s = socket(AF_INET, SOCK_STREAM)
    s.bind((addr, port))
    s.listen(5)
    
    while True:
        client, addr = s.accept()
        data = client.recv(1000000).decode('utf-8')

        print(f'Получено сообщение:\n{data}\nот Клиента с адреса: {addr}')

        if data:
            response_data = parse_client_data(data)
        else:
            response_data = get_response(400, 'Invalid client data')
        
        msg = response_data
        
        client.send(msg.encode('utf-8'))
        client.close()


def main():
    args = get_arguments()

    run_chat_server(args.addr, args.port)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
