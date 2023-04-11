# 2. Задание на закрепление знаний по модулю json.
#   Есть файл orders в формате JSON с информацией о заказах.
#   Написать скрипт, автоматизирующий его заполнение данными. Для этого:
#     1. Создать функцию write_order_to_json(), в которую передается 5 параметров —
#       товар (item), количество (quantity), цена (price), покупатель (buyer), дата (date).
#       Функция должна предусматривать запись данных в виде словаря в файл orders.json.
#       При записи данных указать величину отступа в 4 пробельных символа;
#     2. Проверить работу программы через вызов функции write_order_to_json() с
#       передачей в нее значений каждого параметра.

import json


def write_order_to_json(item, quantity, price, buyer, date):

    with open('orders.json') as f_n:
        objs = json.load(f_n)

    objs['orders'].append({
        'item': item,
        'quantity': quantity,
        'price': price,
        'buyer': buyer,
        'date': date,
    })

    with open('orders.json', 'w') as f_n:
        json.dump(objs, f_n, indent=4)


if __name__ == '__main__':
    write_order_to_json("Laptop", 2, 5000.21, "Andrei", "05/04/2023")
    with open('orders.json') as f:
        print(f.read())
