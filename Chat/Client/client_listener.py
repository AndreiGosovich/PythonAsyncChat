from socket import *

s = socket(AF_INET, SOCK_STREAM)  # Создать сокет TCP
s.connect(('localhost', 7777))  # Соединиться с сервером
while True:  # Постоянный опрос сервера
    msg = s.recv(1024)
    if not msg:
        break
    print("Сообщение от сервера: %s" % msg.decode('utf-8'))

s.close()
