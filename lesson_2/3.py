# 3. Задание на закрепление знаний по модулю yaml.
#   Написать скрипт, автоматизирующий сохранение данных в файле YAML-формата. Для этого:
#     1. Подготовить данные для записи в виде словаря, в котором
#       первому ключу соответствует список,
#       второму — целое число,
#       третьему — вложенный словарь, где значение каждого ключа — это целое число с юникод-символом,
#       отсутствующим в кодировке ASCII (например, €);
#     2. Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml.
#       При этом обеспечить стилизацию файла с помощью параметра default_flow_style,
#       а также установить возможность работы с юникодом: allow_unicode = True;
#     3. Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.

import yaml


def save_to_yaml():
    _list = ['val_1', 'val_2', 'val_3']

    _number = 42

    _symbols = {
        '€': 8364,
        '£': 163,
        '¥': 165,
    }

    data_to_yaml = {'list': _list, 'number': _number, 'symbols': _symbols}

    with open('file.yaml', 'w') as f_n:
        yaml.dump(data_to_yaml, f_n, allow_unicode=True, default_flow_style=False)


if __name__ == '__main__':
    save_to_yaml()
    with open('file.yaml') as f:
        print(f.read())
