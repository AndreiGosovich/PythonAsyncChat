from PyQt6 import QtWidgets, uic
import sys

from PyQt6.QtGui import QStandardItemModel, QStandardItem


class ServerWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.init_ui()
        self.database = None

    def init_ui(self):
        uic.loadUi('gui_main_server.ui', self)
        self.btnExit.clicked.connect(self.close)

    def create_users_list_view(self):
        list_view = QStandardItemModel()
        list_view.setHorizontalHeaderLabels(['id', 'Имя', 'Информация'])
        if self.database:
            list_users = self.database.get_all_users()
            for user in list_users:
                id_ = user.id
                name = user.name
                information = user.information
                id_ = QStandardItem(str(id_))
                id_.setEditable(False)
                name = QStandardItem(name)
                name.setEditable(False)
                information = QStandardItem(information)
                information.setEditable(False)
                list_view.appendRow([id_, name, information])
        return list_view

    def create_messages_history_view(self, database, count=20):
        if self.database:
            messages = database.get_messages_history(count)
            messages_view = QStandardItemModel()
            for message in messages:
                messages_view.appendRow(QStandardItem(f'({message[3]}) {message[0]} -> {message[1]}: {message[2]}'))
            return messages_view


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ServerWindow()
    window.show()
    sys.exit(app.exec())
