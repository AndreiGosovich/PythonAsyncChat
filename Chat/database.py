from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, create_engine, MetaData, Table


class DatabaseStorage:
    Base = declarative_base()

    class Users(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        information = Column(String)

        def __init__(self, name, information=''):
            self.name = name
            self.information = information

        def __repr__(self):
            return self.name

    class UserHistory(Base):
        __tablename__ = 'history'
        id = Column(Integer, primary_key=True)
        user = Column(String)  # login пользователя
        time_login = Column(DateTime)
        ip_address = Column(String)

        def __init__(self, user, ip_address, time_login):
            self.user = user
            self.ip_address = ip_address
            self.time_login = time_login

        def __repr__(self):
            return f'{self.user} logged in {self.time_login} from IP {self.ip_address}'

    class ContactList(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        user_owner = Column(Integer)
        user_contact = Column(Integer)

        def __init__(self, user_owner, user_contact):
            self.user_owner = user_owner
            self.user_contact = user_contact

        def __repr__(self):
            return f'{self.user_owner} has contact {self.user_contact}'


if __name__ == "__main__":
    engine = create_engine('sqlite:///database.sqlite3', echo=True)
    metadata = MetaData()

    users_table = Table('users', metadata,
                        Column('id', Integer, primary_key=True),
                        Column('name', String),
                        Column('information', String),
                        )

    history_table = Table('history', metadata,
                          Column('id', Integer, primary_key=True),
                          Column('user', String),
                          Column('time_login', DateTime),
                          Column('ip_address', String),
                          )

    contacts_table = Table('contacts', metadata,
                           Column('id', Integer, primary_key=True),
                           Column('user_owner', Integer),
                           Column('user_contact', Integer),
                           )

    metadata.create_all(engine)

    session = sessionmaker(bind=engine)()

    username = 'Andrei'
    user = session.query(users_table).filter_by(name=username).first()
    if not user:
        user = DatabaseStorage.Users(username, 'just user')
        session.add(user)
        session.commit()
    print(user.name, user.information, user.id)

