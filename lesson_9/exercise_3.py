# Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
# Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
# (использовать модуль tabulate).
# Таблица должна состоять из двух колонок и выглядеть примерно так:
# Reachable     Unreachable
# ------------- -------------
# 10.0.0.1      10.0.0.3
# 10.0.0.2      10.0.0.4

import ipaddress
import os
import platform
import subprocess

from tabulate import tabulate


def host_ping(address):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    ip_v4 = ipaddress.ip_address(address)

    p = subprocess.Popen(['ping', ip_v4.__str__(), param, '1', '-w', '1'], shell=False, stdout=subprocess.PIPE)
    p.wait()

    if p.returncode == 0:
        return True
    else:
        return False


def host_range_ping_tab(network):
    subnet = ipaddress.ip_network(network)
    result = {
        'Reachable': list(),
        'Unreachable': list(),
    }

    for ip in subnet.hosts():
        result['Reachable'].append(ip.__str__()) if host_ping(ip) else result['Unreachable'].append(ip.__str__())
    print(tabulate(result, headers='keys'))


if __name__ == '__main__':
    try:
        host_range_ping_tab('192.168.1.0/28')
    except Exception as e:
        print(e)
