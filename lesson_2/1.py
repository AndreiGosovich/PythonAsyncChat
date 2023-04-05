# 1. Задание на закрепление знаний по модулю CSV.
#   Написать скрипт, осуществляющий выборку определенных данных из файлов info_1.txt, info_2.txt, info_3.txt
#   и формирующий новый «отчетный» файл в формате CSV. Для этого:
#     1. Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с данными, их открытие
#       и считывание данных. В этой функции из считанных данных необходимо с помощью регулярных выражений извлечь
#       значения параметров «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
#       Значения каждого параметра поместить в соответствующий список. Должно получиться четыре списка —
#       например, os_prod_list, os_name_list, os_code_list, os_type_list. В этой же функции создать главный
#       список для хранения данных отчета — например, main_data — и поместить в него названия столбцов отчета
#       в виде списка: «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
#       Значения для этих столбцов также оформить в виде списка и поместить в файл main_data (также для каждого файла);
#     2. Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл.
#       В этой функции реализовать получение данных через вызов функции get_data(),
#       а также сохранение подготовленных данных в соответствующий CSV-файл;
#     3. Проверить работу программы через вызов функции write_to_csv().

import re
import csv

RE_GET_PARSER = re.compile(r'((?P<os_prod_list>Изготовитель системы)|(?P<os_name_list>Название ОС)|('
                           r'?P<os_code_list>Код продукта)|(?P<os_type_list>Тип системы)):\s+(?P<value>.+)')
FILE_LIST = ('info_1.txt', 'info_2.txt', 'info_3.txt')
FILE_CSV = 'main_data.csv'


def get_data(file_list):
    main_data = [['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']]
    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []

    for file in file_list:
        with open(file, encoding='Windows-1251') as f_n:
            for el_str in f_n:
                for res in RE_GET_PARSER.finditer(el_str):
                    if res.group('os_prod_list'):
                        os_prod_list.append(res.group('value').strip())
                    if res.group('os_name_list'):
                        os_name_list.append(res.group('value').strip())
                    if res.group('os_code_list'):
                        os_code_list.append(res.group('value').strip())
                    if res.group('os_type_list'):
                        os_type_list.append(res.group('value').strip())

    for i in (range(0, len(FILE_LIST))):
        main_data.append([os_prod_list[i], os_name_list[i], os_code_list[i], os_type_list[i]])
    return main_data


def write_to_csv(file_csv):
    with open(file_csv, 'w') as f_n:
        f_n_writer = csv.writer(f_n, quoting=csv.QUOTE_NONNUMERIC)
        f_n_writer.writerows(get_data(FILE_LIST))


if __name__ == '__main__':
    write_to_csv(FILE_CSV)
