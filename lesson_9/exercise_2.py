# Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
# Меняться должен только последний октет каждого адреса.
# По результатам проверки должно выводиться соответствующее сообщение.

import ipaddress
import platform
import subprocess


def host_ping(address_list):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    for ip in address_list:
        try:
            ip_v4 = ipaddress.ip_address(ip)
        except ValueError:
            pass
        else:
            p = subprocess.Popen(['ping', ip_v4.__str__(), param, '1', '-w', '2'], shell=False, stdout=subprocess.PIPE)
            p.wait()
            if p.returncode == 0:
                print(f'Узел {ip_v4} доступен')
            else:
                print(f'Узел {ip_v4} не доступен')


def host_range_ping(network):
    subnet = ipaddress.ip_network(network)

    host_ping(subnet.hosts())


if __name__ == '__main__':
    try:
        host_range_ping('192.168.1.0/28')
    except Exception as e:
        print(e)
