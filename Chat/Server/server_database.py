from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import Column, Integer, String, DateTime, create_engine, MetaData, Table, ForeignKey, desc
from datetime import datetime


class ServerDatabaseStorage:
    Base = declarative_base()

    class Users(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        password_hash = Column(String)
        information = Column(String)

        def __init__(self, name, password_hash, information=''):
            self.name = name
            self.password_hash = password_hash
            self.information = information

        def __repr__(self):
            return self.name

    class UserHistory(Base):
        __tablename__ = 'history'
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Column(Integer)  # id пользователя
        time_login = Column(DateTime)
        ip_address = Column(String)

        user = relationship("Users")

        def __init__(self, user_id, ip_address, time_login):
            self.user_id = user_id
            self.ip_address = ip_address
            self.time_login = time_login

    class ContactList(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        user_owner = Column(Integer, ForeignKey("users.id"), nullable=False)
        user_contact = Column(Integer, nullable=False)

        def __init__(self, user_owner, user_contact):
            self.user_owner = user_owner
            self.user_contact = user_contact

        def __repr__(self):
            return f'{self.user_owner} has contact {self.user_contact}'

    class MessagesHistory(Base):
        __tablename__ = 'messages_history'
        id = Column(Integer, primary_key=True)
        user_id_from = Column(Integer, ForeignKey("users.id"), nullable=False)  # Column(Integer)  # id пользователя
        user_id_to = Column(Integer, ForeignKey("users.id"), nullable=False)  # Column(Integer)  # id пользователя
        message = Column(String)
        time_send = Column(DateTime)

        def __init__(self, user_id_from, user_id_to, message, time_send):
            self.user_id_from = user_id_from
            self.user_id_to = user_id_to
            self.message = message
            self.time_send = time_send

    def __init__(self, connection_string, enable_echo=False):
        self.db_engine = create_engine(connection_string, echo=enable_echo, connect_args={'check_same_thread': False})
        self.metadata = MetaData()
        self.map_tables()
        self.session = sessionmaker(bind=self.db_engine)()

    def change_engine(self, connection_string, enable_echo):
        self.db_engine = create_engine(connection_string, enable_echo, connect_args={'check_same_thread': False})

    def map_tables(self):
        users_table = Table('users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String),
                            Column('password_hash', String),
                            Column('information', String),
                            )

        history_table = Table('history', self.metadata,
                              Column('id', Integer, primary_key=True),
                              Column('user_id', Integer, ForeignKey("users.id"), nullable=False),
                              Column('time_login', DateTime),
                              Column('ip_address', String),
                              )

        contacts_table = Table('contacts', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('user_owner', Integer, ForeignKey("users.id"), nullable=False),
                               Column('user_contact', Integer, ForeignKey("users.id"), nullable=False),
                               )

        messages_history = Table('messages_history', self.metadata,
                                 Column('id', Integer, primary_key=True),
                                 Column('user_id_from', Integer, ForeignKey("users.id"), nullable=False),
                                 Column('user_id_to', Integer, ForeignKey("users.id"), nullable=False),
                                 Column('message', String),
                                 Column('time_send', DateTime),
                                 )

        self.metadata.create_all(self.db_engine)

    @staticmethod
    def get_time():
        return datetime.now()  # calendar.timegm(datetime.now(timezone.utc).utctimetuple())

    def add_user(self, user_name, password_hash, information=''):
        user = self.session.query(self.Users).filter_by(name=user_name).first()
        if not user:
            user = ServerDatabaseStorage.Users(user_name, password_hash, information)
            self.session.add(user)
            self.session.commit()
        return user

    def get_user(self, user_name):
        user = self.session.query(self.Users).filter_by(name=user_name).first()
        return user

    def add_user_to_history(self, user_id, ip_address):
        current_time = self.get_time()
        history = self.UserHistory(user_id, ip_address, current_time)
        self.session.add(history)
        self.session.commit()

    def user_connection(self, user_name, ip_address):
        user = self.get_user(user_name)
        if not user:
            user = self.add_user(user_name)
        self.add_user_to_history(user.id, ip_address)

    def add_contact(self, user_owner, user_contact):
        user = self.get_user(user_owner)
        contact = self.get_user(user_contact)
        if contact and not self.session.query(self.ContactList).filter_by(user_owner=user.id,
                                                                          user_contact=contact.id).count():
            contact_record = self.ContactList(user.id, contact.id)
            self.session.add(contact_record)
            self.session.commit()

    def get_contacts(self, user_owner):
        user = self.get_user(user_owner)
        contact_list = self.session.query(self.ContactList).filter_by(user_owner=user.id).all()
        return tuple(str(self.session.query(self.Users).get(c.user_contact)) for c in contact_list)

    def remove_contact(self, user_owner, user_contact):
        user = self.get_user(user_owner)
        contact = self.get_user(user_contact)
        contact_records = self.session.query(self.ContactList).filter_by(user_owner=user.id, user_contact=contact.id).all()
        if contact and len(contact_records):
            self.session.delete(contact_records[0])
            self.session.commit()

    def save_messge_to_history(self, user_from, user_to, message):
        current_time = self.get_time()
        user = self.get_user(user_from)
        contact = self.get_user(user_to)
        if user and contact:
            self.session.add(self.MessagesHistory(user.id, contact.id, message, current_time))
            self.session.commit()

    def get_all_users(self):
        return self.session.query(self.Users).filter().all()

    def get_messages_history(self, count=20):
        messages = []
        for m in self.session.query(self.MessagesHistory).filter().order_by(desc(self.MessagesHistory.time_send)).limit(count):
            messages.append([
                self.session.query(self.Users).get(m.user_id_from),
                self.session.query(self.Users).get(m.user_id_to),
                m.message,
                m.time_send,
            ])
        return messages

    def get_user_and_password(self, user_name, password_hash):
        result = self.session.query(self.Users).filter_by(name=user_name, password_hash=password_hash).first()
        print(result)
        return result


if __name__ == "__main__":
    username = 'Andrei'
    database = ServerDatabaseStorage('sqlite:///server_database.sqlite3', True)
    user_1 = database.add_user(username, '123')

    print(user_1)
    print(*database.get_all_users())
    print(*database.get_messages_history())




