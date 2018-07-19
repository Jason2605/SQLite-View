from datetime import timedelta
from flask import Flask
from flask_login import LoginManager
from SQLite_View.helpers.database import Login
import os

app = Flask(__name__)
app.permanent_session_lifetime = timedelta(minutes=10)
app.config["SECRET_KEY"] = b'\xc4\xc0\xec\xba}\xe5"N\xaep\xfe\xf5\xae(\xa3\x8fYo^\xbc9{\xe2J'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

user_database = Login(not os.path.isfile("sqlite-view.db"))

header_array = [
    ["Home", "/home/", "home"],
    ["Users", "/users/", "account_circle"],
    ["Logout", "/logout/", "input"]
]


from SQLite_View import views
