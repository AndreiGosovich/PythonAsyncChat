# logging - стандартный модуль для организации логирования
import logging

# Можно выполнить более расширенную настройку логирования.
# Создаем объект-логгер:
logger = logging.getLogger('chat.client')

# Создаем объект форматирования:
formatter = logging.Formatter("%(asctime)s %(levelname)s %(module)s %(message)s")

# Создаем файловый обработчик логирования (можно задать кодировку):
file_handler = logging.FileHandler("chat.client.log", encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.CRITICAL)
stream_handler.setFormatter(formatter)

# Добавляем в логгер новый обработчик событий и устанавливаем уровень логирования
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    # Создаем потоковый обработчик логирования (по умолчанию sys.stderr):
    # console = logging.StreamHandler()
    # console.setLevel(logging.DEBUG)
    # console.setFormatter(formatter)
    # logger.addHandler(console)
    logger.info('Тестовый запуск логирования Client')
