# Написать функцию **host_ping()**, в которой с помощью утилиты **ping** будет проверяться доступность сетевых узлов.
# Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
#
#     В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
#     («Узел доступен», «Узел недоступен»).
#     При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().

import ipaddress
import platform
import subprocess

ADDRESS_LIST = (
    '216.58.210.142',
    '77.88.55.242',
    '127.0.0.1',
    '94.100.100.200',
    '110.55.78.34',
    '10.100.125.2',
    'ya.ru',
    'mail.ru'
)


def host_ping(address_list):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    for ip in address_list:
        try:
            ip_v4 = ipaddress.ip_address(ip)
        except ValueError:
            pass
        else:
            p = subprocess.Popen(['ping', ip_v4.__str__(), param, '1', '-w', '3'], shell=False, stdout=subprocess.PIPE)
            p.wait()
            if p.returncode == 0:
                print(f'Узел {ip_v4} доступен')
            else:
                print(f'Узел {ip_v4} не доступен')


if __name__ == '__main__':
    try:
        host_ping(ADDRESS_LIST)
    except Exception as e:
        print(e)
