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

    def __fetch_user(self, query, parameter):
        cursor = self.connection.cursor()

        cursor.execute(query, (parameter,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            rowid, username, password = user
            return User(rowid, username, password)

    def fetch_user_username(self, username):
        sql_fetch_user = "SELECT rowid, username, password FROM User WHERE username = ?"
        return self.__fetch_user(sql_fetch_user, username)

    def fetch_user_id(self, user_id):
        sql_fetch_user = "SELECT rowid, username, password FROM User WHERE rowid = ?"
        return self.__fetch_user(sql_fetch_user, user_id)

    def insert_user(self, username, password):
        cursor = self.connection.cursor()

        sql_insert_user = "INSERT INTO User VALUES (?, ?)"
        cursor.execute(sql_insert_user, (username, password))
        self.connection.commit()
        cursor.close()

        self.users.append(username)

    def delete_user(self, username):
        cursor = self.connection.cursor()

        sql_insert_user = "DELETE FROM User WHERE username = ?"
        cursor.execute(sql_insert_user, (username,))
        self.connection.commit()
        cursor.close()

        self.users.remove(username)

    def edit_user(self, username="", password="", current_username=""):
        cursor = self.connection.cursor()

        if username and password:
            sql_edit_user = "UPDATE User SET username = ?, password = ? WHERE username = ?"
            parameters = (username, password, current_username)

            self.users.remove(current_username)
            self.users.append(username)
        elif username:
            sql_edit_user = "UPDATE User SET username = ? WHERE username = ?"
            parameters = (username, current_username)

            self.users.remove(current_username)
            self.users.append(username)
        else:
            sql_edit_user = "UPDATE User SET password = ? WHERE username = ?"
            parameters = (password, current_username)

        cursor.execute(sql_edit_user, parameters)
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
