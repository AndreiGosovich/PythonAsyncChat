# Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления в байтовое
# и выполнить обратное преобразование (используя методы encode и decode).

print('Задание 4:')

DATA = ('разработка', 'администрирование', 'protocol', 'standard')

for val in DATA:
    print(f'{val} == {val.encode(encoding="UTF-8")} == {val.encode(encoding="UTF-8").decode(encoding="UTF-8")}')

print('=================================================')

