from setuptools import setup, find_packages

setup(name="GAM_chat_client",
      version="0.1.1",
      description="Тестовый проект",
      author="Andrei G.",
      author_email="andrei_gosovich@mail.ru",
      packages=find_packages(),
      install_requires=['PyQt6', 'sqlalchemy']
      )
