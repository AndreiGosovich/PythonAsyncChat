from PyQt6 import QtWidgets, uic
import sys

from PyQt6.QtGui import QStandardItemModel, QStandardItem


class ClientWindow(QtWidgets.QMainWindow):
    def __init__(self, username='', addr='', port='', parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.username = username
        self.addr = addr
        self.port = port
        self.init_ui()
        self.database = None

    def init_ui(self):
        uic.loadUi('gui/gui_client_main_window.ui', self)
        self.btnExit.clicked.connect(self.close)
        if self.username:
            self.edtUserName.insert(self.username)
        self.edtAddres.insert(self.addr)
        self.edtPort.insert(str(self.port))

    def get_contacts_view(self):
        if self.database:
            contacts = self.database.get_contacts(self.username)
            contacts_view = QStandardItemModel()
            for contact in contacts:
                contacts_view.appendRow(QStandardItem(contact.user_contact))
            return contacts_view


class ChatDialogWindow(QtWidgets.QDialog):
    def __init__(self, contact, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.username = parent.username
        self.contact = contact
        self.init_ui()

    def init_ui(self):
        uic.loadUi('gui/gui_client_chat_window.ui', self)
        self.edtUserName.insert(self.contact)
        self.setWindowTitle(f'Чат с {self.contact}')

    def create_messages_history_view(self, user_to):
        messages = self.parent().database.get_message_history(self.username, user_to)
        messages_view = QStandardItemModel()
        for message in messages:
            messages_view.appendRow(QStandardItem(f'<{message[3].strftime("%Y-%m-%d %H:%M:%S")}> {message[0]}: {message[2]}'))
        return messages_view


class AddContactDialogWindow(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.init_ui()

    def init_ui(self):
        uic.loadUi('gui/gui_client_add_contact_window.ui', self)


class DelContactDialogWindow(QtWidgets.QDialog):
    def __init__(self, contact, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.contact = contact
        self.init_ui()

    def init_ui(self):
        uic.loadUi('gui/gui_client_del_contact_window.ui', self)
        html = f'<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;' \
               f' -qt-block-indent:0; text-indent:0px;"><span style=" font-size:14pt; font-weight:700;">' \
               f'{self.contact}</span></p>'
        self.edtUserName.setHtml(html)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ClientWindow("Andrei")
    window.show()
    sys.exit(app.exec())
