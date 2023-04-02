# Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из
# байтовового в строковый тип на кириллице.

import subprocess
import chardet


def ping(url, count_pings=5):
    args = ['ping', url]
    subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)
    for line in subproc_ping.stdout:
        encoding = chardet.detect(line)['encoding']
        line = line.decode(encoding).encode('utf-8')
        print(line.decode('utf-8'), end='')
        if not count_pings:
            return 0
        count_pings -= 1


print('Задание 5:')

ping('yandex.ru', 3)
print('')
ping('youtube.com', 3)


print('=================================================')

