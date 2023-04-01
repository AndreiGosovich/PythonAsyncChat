# Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления в байтовое
# и выполнить обратное преобразование (используя методы encode и decode).

print('Задание 4:')

var_1 = 'разработка'
var_2 = 'администрирование'
var_3 = 'protocol'
var_4 = 'standard'

print('STRINGS:')
print('var_1:', var_1)
print('var_2:', var_2)
print('var_3:', var_3)
print('var_4:', var_4)

var_1_bytes = var_1.encode(encoding='UTF-8')
var_2_bytes = var_2.encode(encoding='UTF-8')
var_3_bytes = var_3.encode(encoding='UTF-8')
var_4_bytes = var_4.encode(encoding='UTF-8')

print('')
print('BYTES:')
print('var_1_bytes:', var_1_bytes)
print('var_2_bytes:', var_2_bytes)
print('var_3_bytes:', var_3_bytes)
print('var_4_bytes:', var_4_bytes)

var_1_bytes_string = var_1_bytes.decode(encoding='UTF-8')
var_2_bytes_string = var_2_bytes.decode(encoding='UTF-8')
var_3_bytes_string = var_3_bytes.decode(encoding='UTF-8')
var_4_bytes_string = var_4_bytes.decode(encoding='UTF-8')

print('')
print('STRINGS:')
print('var_1_bytes_string:', var_1_bytes_string)
print('var_2_bytes_string:', var_2_bytes_string)
print('var_3_bytes_string:', var_3_bytes_string)
print('var_4_bytes_string:', var_4_bytes_string)

print('=================================================')

