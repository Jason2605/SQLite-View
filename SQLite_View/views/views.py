from SQLite_View import app, user_database, login_manager, header_array
from flask import render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_login import login_required, logout_user, login_user
from passlib.hash import bcrypt
from werkzeug.utils import secure_filename
import sqlite3
import glob
import re
import os
import json


@login_manager.user_loader
def load_user(user_id):
    return user_database.fetch_user_id(user_id)


@app.before_request
def refresh_session():
    session.modified = True


@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "GET":

        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    if not username or not password:
        return redirect(url_for("login"))

    user_obj = user_database.fetch_user(username)

    if not user_obj:
        return redirect(url_for("login"))

    if bcrypt.verify(password, user_obj.password):
        login_user(user_obj)
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route('/home/')
@login_required
def home():
    databases = [x.replace("databases/", "") for x in glob.glob("databases/*.db")]
    return render_template("home.html", header_array=header_array, databases=databases)


@app.route('/users/')
@login_required
def users():
    all_users = user_database.fetch_all_users()
    return render_template("users.html", header_array=header_array, users=all_users)


@app.route('/users/create/', methods=["POST"])
@login_required
def users_create():
    username = request.form["username"]
    password = request.form["password"]

    if username and password:
        if username not in user_database.users:
            hashed_password = bcrypt.hash(password)
            user_database.insert_user(username, hashed_password)
            return jsonify(status_code=200)

        return jsonify(status_code=403, error="Username already exists!")
    return jsonify(status_code=403, error="Username and/or password not supplied!")


@app.route('/upload/', methods=["POST"])
@login_required
def upload():
    file = request.files['file']
    if file and file.filename.endswith(".db"):
        filename = secure_filename(file.filename)
        path = os.path.join("databases/", filename)
        if os.path.exists(path):
            return "FILE EXISTS!"
        file.save(path)
        return redirect(url_for("home"))
    return "ohno"


@app.route('/download/sql/', methods=["POST"])
@login_required
def download_sql():
    database = request.form["database"]
    database_path = "databases/{}".format(request.form["database"])
    sql_path = database.replace(".db", ".sql")
    c = sqlite3.connect(database_path)

    with open("dumps/{}".format(sql_path), 'w') as f:
        for line in c.iterdump():
            f.write('{}\n'.format(line))

    return send_from_directory(os.path.join(os.getcwd(), "dumps"), sql_path, as_attachment=True)


@app.route('/tables/<database>')
@login_required
def find_tables(database):
    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [x[0] for x in cursor.fetchall()]
    session["tables"] = all_tables
    cursor.close()
    connection.close()

    return render_template("tables.html", header_array=header_array, tables=all_tables, database=database)


def to_json(data, columns):
    json_list = []
    for row in data:
        json_list.append(dict(zip(columns, row)))
    return json_list


@app.route('/tables/<table>/<database>')
@login_required
def tables(database, table):
    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()

    if table not in session["tables"]:
        return "ERROR!!!"

    cursor.execute("SELECT sql FROM sqlite_master WHERE tbl_name = ?", (table,))
    table_sql = [x[0] for x in cursor.fetchall() if x[0] is not None]
    indexes = table_sql[1:]

    pattern = re.compile("CREATE INDEX (.*) ON .* \(?([^\)]*)")
    found_indexes = []
    for index in indexes:
        found_indexes.extend(pattern.findall(index))

    cursor.execute("SELECT * FROM {}".format(table))
    data = cursor.fetchall()

    cursor.execute("PRAGMA TABLE_INFO({})".format(table))
    table_data = [x[1:] for x in cursor.fetchall()]
    columns = [x[0] for x in table_data]

    json_data = json.dumps(to_json(data, columns), indent=4)

    cursor.close()
    connection.close()

    return render_template("view_table.html",
                           header_array=header_array,
                           table=table,
                           table_columns=columns,
                           data=data,
                           table_schema=table_sql[0],
                           sql_indexes="\n".join(indexes),
                           indexes=found_indexes,
                           table_data=table_data,
                           json_data=json_data)


@app.route('/delete/', methods=["POST"])
@login_required
def delete():
    database = "databases/{}".format(request.form["database"])
    if not os.path.exists(database):
        return jsonify(status_code=403, error="Database does not exist!")
    os.remove(database)
    return jsonify(status_code=200)


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))
