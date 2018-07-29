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

    user_obj = user_database.fetch_user_username(username)

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


@app.route('/users/delete/', methods=["POST"])
@login_required
def users_delete():
    username = request.form["username"]

    if username:
        if username in user_database.users:
            user_database.delete_user(username)
            return jsonify(status_code=200)
        return jsonify(status_code=403, error="User does not exist!")
    return jsonify(status_code=403, error="Username not supplied!")


@app.route('/users/edit/', methods=["POST"])
@login_required
def users_edit():
    current_username = request.form["current_username"]
    username = request.form["username"]
    password = request.form["password"]

    if password:
        password = bcrypt.hash(password)

    if username or password:
        if current_username != username:
            if username in user_database.users:
                return jsonify(status_code=403, error="Username already exists!")
        else:
            username = ""

        user_database.edit_user(username, password, current_username)
        return jsonify(status_code=200)
    return jsonify(status_code=403, error="Username or password not supplied!")


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


@app.route('/tables/column/add/', methods=["POST"])
@login_required
def add_column():
    database = request.form["database"]
    table = request.form["table"]
    name = request.form["name"]
    data_type = request.form["type"]
    allow_null = request.form["null"]
    default_value = request.form["default"]

    if " " in default_value and data_type == "TEXT":
        default_value = "'{}'".format(default_value.replace("'", "''"))

    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()

    sql_add_column = "ALTER TABLE {} ADD COLUMN {} {} {} {}".format(
        table, name, data_type,
        "NOT NULL" if allow_null == "false" else "",
        "DEFAULT {}".format(default_value) if default_value != "" else "").strip()

    try:
        session["columns"].append(name)
        cursor.execute(sql_add_column)
        connection.commit()
    except sqlite3.OperationalError as e:
        return jsonify(status_code=403, error=str(e))
    finally:
        cursor.close()
        connection.close()

    return jsonify(status_code=200)


@app.route('/tables/column/delete/', methods=["POST"])
@login_required
def delete_column():
    database = request.form["database"]
    table = request.form["table"]
    name = request.form["name"]

    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()

    cursor.execute("SELECT sql FROM sqlite_master WHERE tbl_name = ?", (table,))
    sql = [x[0] for x in cursor.fetchall() if x[0] is not None]
    table_schema = sql[0]
    column_index = table_schema.find("(")
    table_schema_columns = table_schema[column_index:].split(",")

    for index, column in enumerate(table_schema_columns):
        if name in column:
            del table_schema_columns[index]

    table_schema = "{}{}".format(table_schema[:column_index], ",".join(table_schema_columns))

    if not table_schema.endswith(")"):
        table_schema += "\n)"

    try:
        session["columns"].remove(name)
        cursor.execute("ALTER TABLE {} RENAME TO tmp".format(table))
        cursor.execute(table_schema)
        cursor.execute("INSERT INTO {} SELECT {} FROM tmp".format(table, ", ".join(session["columns"])))
        cursor.execute("DROP TABLE tmp")

        for index in sql[1:]:
            if not "({})".format(name) in index:
                cursor.execute(index)

        connection.commit()
    except sqlite3.OperationalError as e:
        return jsonify(status_code=403, error=str(e))
    finally:
        cursor.close()
        connection.close()

    return jsonify(status_code=200)


@app.route('/tables/column/rename/', methods=["POST"])
@login_required
def rename_column():
    database = request.form["database"]
    table = request.form["table"]
    old_name = request.form["old_name"]
    new_name = request.form["name"]

    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()

    cursor.execute("SELECT sql FROM sqlite_master WHERE tbl_name = ?", (table,))
    sql = [x[0] for x in cursor.fetchall() if x[0] is not None]

    table_schema = sql[0].replace(" {} ".format(old_name), " {} ".format(new_name))

    try:
        tmp = session["columns"][:]
        tmp.remove(old_name)
        tmp.append(new_name)

        cursor.execute("ALTER TABLE {} RENAME TO tmp".format(table))
        cursor.execute(table_schema)
        cursor.execute("INSERT INTO {}({}) SELECT {} FROM tmp".format(table, ", ".join(tmp), ", ".join(session["columns"])))
        cursor.execute("DROP TABLE tmp")

        for index in sql[1:]:
            index = index.replace("({})".format(old_name), "({})".format(new_name))
            cursor.execute(index)

        connection.commit()

        session["columns"] = tmp
    except sqlite3.OperationalError as e:
        return jsonify(status_code=403, error=str(e))
    finally:
        cursor.close()
        connection.close()

    return jsonify(status_code=200)


@app.route('/tables/rows/edit/', methods=["POST"])
@login_required
def edit_row():
    form_data = request.form.to_dict()
    database = form_data.pop("database")
    table = form_data.pop("table")
    row_id = form_data.pop("rowid")

    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()

    sql_update_row = "UPDATE {} SET {} WHERE rowid = ?".format(table,
                                                               "{}{}".format(" = ?, ".join(form_data.keys()),
                                                                             " = ?"))
    values = list(form_data.values())
    values.append(row_id)

    try:
        cursor.execute(sql_update_row, values)
        connection.commit()
    except sqlite3.OperationalError as e:
        return jsonify(status_code=403, error=str(e))
    finally:
        cursor.close()
        connection.close()

    return jsonify(status_code=200)


@app.route('/tables/rows/delete/', methods=["POST"])
@login_required
def delete_row():
    database = request.form["database"]
    table = request.form["table"]
    rowid = request.form["rowid"]

    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()
    sql_delete_row = "DELETE FROM {} WHERE rowid = {}".format(table, rowid)

    try:
        cursor.execute(sql_delete_row)
        connection.commit()
    except sqlite3.OperationalError as e:
        return jsonify(status_code=403, error=str(e))
    finally:
        cursor.close()
        connection.close()

    return jsonify(status_code=200)


@app.route('/tables/index/add/', methods=["POST"])
@login_required
def add_index():
    database = request.form["database"]
    table = request.form["table"]
    name = request.form["name"]
    column = request.form["column"]

    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()

    try:
        sql_create_index = "CREATE INDEX {} ON {} (test)".format(name, table, column)
        cursor.execute(sql_create_index)
        connection.commit()
    except sqlite3.OperationalError as e:
        return jsonify(status_code=403, error=str(e))
    finally:
        cursor.close()
        connection.close()

    return jsonify(status_code=200)


def to_json(data, columns):
    json_list = []
    for row in data:
        json_list.append(dict(zip(columns, row)))
    return json_list


@app.route('/tables/<table>/<database>/<int:page>/')
@app.route('/tables/<table>/<database>/<int:page>/<json_data>/')
@login_required
def table_data(table, database, page, json_data=False):

    if table not in session["tables"]:
        return "ERROR!!!"

    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()

    cursor.execute("SELECT *, rowid FROM {} LIMIT ?, ?".format(table), ((page - 1) * 50, 50))
    data = cursor.fetchall()
    length = len(data)

    if json_data:
        data = json.dumps(to_json(data, session["columns"]), indent=4)

    return jsonify(status_code=200, data=data, length=length)


@app.route('/tables/<table>/<database>/')
@login_required
def tables(database, table):

    if table not in session["tables"]:
        return "ERROR!!!"

    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()

    cursor.execute("SELECT sql FROM sqlite_master WHERE tbl_name = ?", (table,))
    table_sql = [x[0] for x in cursor.fetchall() if x[0] is not None]
    indexes = table_sql[1:]

    pattern = re.compile("CREATE INDEX (.*) ON .* \(?([^\)]*)")
    found_indexes = []
    for index in indexes:
        found_indexes.extend(pattern.findall(index))

    cursor.execute("SELECT *, rowid FROM {} LIMIT 0, 50".format(table))
    data = cursor.fetchall()

    cursor.execute("PRAGMA TABLE_INFO({})".format(table))
    table_data = [x[1:] for x in cursor.fetchall()]
    columns = [x[0] for x in table_data]
    session["columns"] = columns
    session["indexes"] = found_indexes

    json_data = json.dumps(to_json(data, columns), indent=4)

    cursor.close()
    connection.close()

    return render_template("view_table.html",
                           header_array=header_array,
                           database=database,
                           table=table,
                           table_columns=columns,
                           data=data,
                           table_schema=table_sql[0],
                           sql_indexes="\n".join(indexes),
                           indexes=found_indexes,
                           table_data=table_data,
                           json_data=json_data)


@app.route('/execute/', methods=["POST"])
@login_required
def execute_query():
    database = request.form["database"]
    query = request.form["query"]

    connection = sqlite3.connect("".join(("databases/", database)), check_same_thread=False)
    cursor = connection.cursor()

    try:
        cursor.execute(query)
        if query.lower().startswith("select"):
            return jsonify(status_code=200, data=cursor.fetchall())
        connection.commit()
        return jsonify(status_code=200, data="")
    except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        return jsonify(status_code=403, error=str(e))
    finally:
        cursor.close()
        connection.close()


@app.route('/delete/', methods=["POST"])
@login_required
def delete():
    database = "databases/{}".format(request.form["database"])
    if not os.path.exists(database):
        return jsonify(status_code=403, error="Database does not exist!")
    os.remove(database)
    return jsonify(status_code=200)


@app.route('/delete/table/', methods=["POST"])
@login_required
def delete_table():
    database = "databases/{}".format(request.form["database"])
    table = request.form["table"]

    if not os.path.exists(database):
        return jsonify(status_code=403, error="Database does not exist!")

    connection = sqlite3.connect(database, check_same_thread=False)
    cursor = connection.cursor()

    if table in session["tables"]:
        cursor.execute("DROP TABLE {}".format(table))
        return jsonify(status_code=200)
    return jsonify(status_code=403, error="Table does not exist!")


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


