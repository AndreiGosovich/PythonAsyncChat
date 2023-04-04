# Каждое из слов «разработка», «сокет», «декоратор» представить в строковом формате и проверить тип и содержание
# соответствующих переменных. Затем с помощью онлайн-конвертера преобразовать строковые представление в формат Unicode
# и также проверить тип и содержимое переменных.

print('Задание 1:')

development = 'разработка'
socket = 'сокет'
decorator = 'декоратор'

print(development, type(development))
print(socket, type(socket))
print(decorator, type(decorator))

print('')

development_unicode = '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430'
socket_unicode = '\u0441\u043e\u043a\u0435\u0442'
decorator_unicode = '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'

print(development_unicode, type(development_unicode))
print(socket_unicode, type(socket_unicode))
print(decorator_unicode, type(decorator_unicode))

print('=================================================')
