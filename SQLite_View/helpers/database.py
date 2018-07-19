import sqlite3
from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, rowid, username, password):
        self.id = rowid
        self.username = username
        self.password = password
        self.connection = None


class Login:
    def __init__(self, create=False):
        self.connection = sqlite3.connect("sqlite-view.db", check_same_thread=False)
        self.users = self.fetch_all_users()
        if create:
            self.__setup()

    def fetch_all_users(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT username FROM User")
        users = [x[0] for x in cursor.fetchall()]
        cursor.close()
        return users

    def fetch_user(self, username):
        cursor = self.connection.cursor()

        sql_fetch_user = "SELECT rowid, username, password FROM User WHERE username = ?"
        cursor.execute(sql_fetch_user, (username,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            rowid, username, password = user
            return User(rowid, username, password)

    def fetch_user_id(self, user_id):
        cursor = self.connection.cursor()

        sql_fetch_user = "SELECT rowid, username, password FROM User WHERE rowid = ?"
        cursor.execute(sql_fetch_user, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            rowid, username, password = user
            return User(rowid, username, password)

    def insert_user(self, username, password):
        cursor = self.connection.cursor()

        sql_insert_user = "INSERT INTO User VALUES (?, ?)"
        cursor.execute(sql_insert_user, (username, password))
        self.connection.commit()
        cursor.close()

    def __setup(self):
        cursor = self.connection.cursor()

        sql_setup_user_table = """
        CREATE TABLE IF NOT EXISTS User (
          username TEXT UNIQUE,
          password TEXT
        ) 
        """

        sql_insert_test_user = """
        INSERT INTO User VALUES ('test', '$2b$12$3uh/dal.fZBM.R2b/2.tFuRlHXO8Bx9xzet781sQ4Wt9RJpuau3VG')
        """

        cursor.execute(sql_setup_user_table)
        cursor.execute(sql_insert_test_user)
        self.connection.commit()
        cursor.close()

    def test(self):

        print("test")

        cursor = self.connection.cursor()

        sql_setup_user_table = """
        CREATE TABLE IF NOT EXISTS User_test (
          username TEXT UNIQUE,
          password TEXT,
          test INTEGER
        ) 
        """

        cursor.execute(sql_setup_user_table)
        self.connection.commit()
        cursor.close()
