from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, create_engine, MetaData, Table, or_, and_
from datetime import datetime
from sqlalchemy.sql import default_comparator


class ClientDatabaseStorage:
    Base = declarative_base()

    class ContactList(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        user_owner = Column(String, nullable=False)
        user_contact = Column(String, nullable=False)

        def __init__(self, user_owner, user_contact):
            self.user_owner = user_owner
            self.user_contact = user_contact

        def __repr__(self):
            return self.user_contact

    class MessagesHistory(Base):
        __tablename__ = 'messages_history'
        id = Column(Integer, primary_key=True)
        user_from = Column(String, nullable=False)
        user_to = Column(String, nullable=False)
        message = Column(String)
        time_send = Column(DateTime)

        def __init__(self, user_from, user_to, message, time_send):
            self.user_from = user_from
            self.user_to = user_to
            self.message = message
            self.time_send = time_send

    def __init__(self, connection_string, enable_echo=False):
        self.db_engine = create_engine(connection_string, echo=enable_echo, connect_args={'check_same_thread': False})
        self.metadata = MetaData()
        self.map_tables()
        self.session = sessionmaker(bind=self.db_engine)()

    def change_engine(self, connection_string, enable_echo):
        self.db_engine = create_engine(connection_string, enable_echo)

    def map_tables(self):
        contacts_table = Table('contacts', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('user_owner', String, nullable=False),
                               Column('user_contact', String, nullable=False),
                               )

        messages_history = Table('messages_history', self.metadata,
                                 Column('id', Integer, primary_key=True),
                                 Column('user_from', String, nullable=False),
                                 Column('user_to', String, nullable=False),
                                 Column('message', String),
                                 Column('time_send', DateTime),
                                 )

        self.metadata.create_all(self.db_engine)

    @staticmethod
    def get_time() -> datetime:
        return datetime.now()  # calendar.timegm(datetime.now(timezone.utc).utctimetuple())

    def add_contact(self, user_owner, user_contact):
        if not self.session.query(self.ContactList).filter_by(user_owner=user_owner, user_contact=user_contact).count():
            contact_record = self.ContactList(user_owner, user_contact)
            self.session.add(contact_record)
            self.session.commit()

    def get_contacts(self, user_owner):
        contact_list = self.session.query(self.ContactList).filter_by(user_owner=user_owner).all()
        return [c for c in contact_list]

    def remove_all_contacts(self):
        contact_list = self.session.query(self.ContactList).filter().all()
        for contact in contact_list:
            self.session.delete(contact)

    def save_message_to_history(self, user_from, user_to, message):
        current_time = self.get_time()
        self.session.add(self.MessagesHistory(user_from, user_to, message, current_time))
        self.session.commit()

    def get_message_history(self, user_from, user_to):
        result = self.session.query(self.MessagesHistory).filter(or_(and_(self.MessagesHistory.user_from == user_from,
                                                                 self.MessagesHistory.user_to == user_to),
                                                                     and_(self.MessagesHistory.user_from == user_to,
                                                                 self.MessagesHistory.user_to == user_from))).all()
        return [[m.user_from, m.user_to, m.message, m.time_send] for m in result]


if __name__ == "__main__":
    username = 'Andrei'
    database = ClientDatabaseStorage('sqlite:///client_database.sqlite3', False)

    database.add_contact('Andrei', 'Sergei')
    database.add_contact('Andrei', 'Vadim')

    print(database.get_contacts('Andrei'))

    # database.save_message_to_history('Andrei', 'Vadim', 'Hi')
    # database.save_message_to_history('Andrei', 'Sergei', 'Hello')

    database.remove_all_contacts()

    print(database.get_message_history('Andrei'))

    print(database.get_contacts('Andrei'))
