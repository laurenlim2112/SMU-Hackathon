from flask import Flask, flash, request, redirect, render_template, session, url_for, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

import sqlite3, os, pandas, datetime

app = Flask(__name__)
app.secret_key = os.urandom(12)

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    user = cursor.execute("SELECT name FROM users WHERE id = ?", [id]).fetchone()
    name = user["name"]
    connection.close()
    return render_template("home.html", name=name)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Name cannot be left blank!")
            return render_template("register.html")
        email = request.form.get("email")
        if not email:
            flash("Email cannot be left blank!")
            return render_template("register.html")
        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()
        existing = cursor.execute("SELECT * FROM users WHERE email = ?", [email]).fetchall()
        if len(existing) > 0:
            flash("Email already in use!")
            return render_template("register.html")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password or not confirmation:
            flash("Password and confirmation cannot be left blank!")
            return render_template("register.html")
        if password != confirmation:
            flash("Passwords do not match!")
            return render_template("register.html")
        hashed_password = generate_password_hash(password)
        rate = request.form.get("rate")
        cursor.execute("INSERT INTO users (name, email, hash, rate) VALUES(?, ?, ?, ?)", 
                       [name, email, hashed_password, rate])
        connection.commit()
        connection.close()
        flash("Registration successful!")
        return redirect(url_for("home"))
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email:
            flash("Email needed!")
            return render_template("login.html")
        elif not password:
            flash("No password")
            return render_template("login.html")
        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        result = cursor.execute("SELECT * FROM users WHERE email = ?", [email]).fetchall()
        if len(result) != 1 or not check_password_hash(result[0]["hash"], password):
            flash("Invalid email address and/or password")
            return render_template("login.html")
        session["user_id"] = result[0]["id"]
        cursor.execute("UPDATE users SET rate = 600 WHERE name = ?", ["Rosa"])
        connection.commit()
        connection.close()
        flash("Login successful!")
        return redirect(url_for("home"))
    else:
        return render_template("login.html")
    
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/addclient", methods=["POST"])
@login_required
def addclient():
    name = request.form.get("name")
    email = request.form.get("email")
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    result = cursor.execute("SELECT * FROM clients WHERE email = ?", [email]).fetchall()
    if len(result) > 0:
        flash("Client already in system!")
        return redirect(url_for("home"))
    cursor.execute("INSERT INTO clients (name, email, in_progress, payment_pending, payment_received) VALUES (?, ?, ?, ?, ?)", 
                   [name, email, 0, 0, 0])
    user_id = session["user_id"]
    client_id = cursor.execute("SELECT * FROM clients WHERE email = ?", [email]).fetchone()["id"]
    cursor.execute("INSERT INTO users_clients (user_id, client_id) VALUES (?, ?)", [user_id, client_id])
    connection.commit()
    connection.close()
    flash("Client added successfully!")
    return redirect(url_for("dashboard"))

@app.route("/addlawyer/<id>", methods=["POST"])
@login_required
def addlawyer(id):
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    rel = cursor.execute("SELECT * FROM users_clients WHERE user_id = ? AND client_id = ?", [user_id, id]).fetchall()
    if len(rel) != 0:
        new_lawyer_id = request.form.get("id")
        cursor.execute("INSERT INTO users_clients (user_id, client_id) VALUES (?, ?)", [new_lawyer_id, id])
        connection.commit()
        connection.close()
        return redirect(url_for("client", id=id))
    else:
        flash("You are not authorised to add lawyers for this client!")
        return redirect(url_for("home"))

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    clients = []
    rows = cursor.execute("SELECT * FROM users_clients WHERE user_id = ?", [user_id]).fetchall()
    for row in rows:
        client_id = row["client_id"]
        client_info = cursor.execute("SELECT * FROM clients WHERE id = ?", [client_id]).fetchone()
        client = {}
        client["name"] = client_info["name"]
        client["id"] = client_info["id"]
        client["in_progress"] = client_info["in_progress"]
        client["payment_pending"] = client_info["payment_pending"]
        client["payment_received"] = client_info["payment_received"]
        clients.append(client)
    connection.close()
    return render_template("dashboard.html", clients=clients)

@app.route("/clients/<id>", methods=["GET"])
@login_required
def client(id):
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    user_id = session["user_id"]
    rel = cursor.execute("SELECT * FROM users_clients WHERE user_id = ? AND client_id = ?", [user_id, id]).fetchall()
    if len(rel) != 0:
        client_info = cursor.execute("SELECT * FROM clients WHERE id = ?", [id]).fetchone()
        client = {}
        client["name"] = client_info["name"]
        client["id"] = client_info["id"]
        client["email"] = client_info["email"]
        in_progress_rows = cursor.execute("SELECT * FROM timesheets WHERE client_id = ? AND status = 1", [client_info["id"]]).fetchall()
        in_progress_timesheets = []
        for row in in_progress_rows:
            in_progress_timesheet = {}
            in_progress_timesheet["id"] = row["id"]
            in_progress_timesheet["created"] = row["created"]
            in_progress_timesheets.append(in_progress_timesheet)
        payment_pending_rows = cursor.execute("SELECT * FROM timesheets WHERE client_id = ? AND status = 2", [client_info["id"]]).fetchall()
        payment_pending_timesheets = []
        for row in payment_pending_rows:
            payment_pending_timesheet = {}
            payment_pending_timesheet["id"] = row["id"]
            payment_pending_timesheet["created"] = row["created"]
            payment_pending_timesheets.append(payment_pending_timesheet)
        payment_received_rows = cursor.execute("SELECT * FROM timesheets WHERE client_id = ? AND status = 3", [client_info["id"]]).fetchall()
        payment_received_timesheets = []
        for row in payment_received_rows:
            payment_received_timesheet = {}
            payment_received_timesheet["id"] = row["id"]
            payment_received_timesheet["created"] = row["created"]
            payment_received_timesheets.append(payment_received_timesheet)
        lawyers = cursor.execute("SELECT * FROM users").fetchall()
        connection.close()
        return render_template("client.html", client=client, 
                            in_progress_timesheets=in_progress_timesheets, 
                            payment_pending_timesheets=payment_pending_timesheets, 
                            payment_received_timesheets=payment_received_timesheets,
                            lawyers=lawyers)
    else:
        flash("You are not authorised to view this client's timesheets!")
        return redirect(url_for("home"))

@app.route("/timesheets/<id>", methods=["GET"])
@login_required
def timesheet(id):
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    timesheet = cursor.execute("SELECT * FROM timesheets WHERE id = ?", [id]).fetchone()
    client_id = timesheet["client_id"]
    user_id = session["user_id"]
    rel = cursor.execute("SELECT * FROM users_clients WHERE user_id = ? AND client_id = ?", [user_id, client_id]).fetchall()
    if len(rel) != 0:
        client = cursor.execute("SELECT * FROM clients WHERE id = ?", [client_id]).fetchone()
        rows = cursor.execute("SELECT * FROM tasks WHERE timesheet_id = ?", [id]).fetchall()
        tasks = []
        for row in rows:
            task = {}
            lawyer_info = cursor.execute("SELECT * FROM users WHERE id = ?", [row["user_id"]]).fetchone()
            task["lawyer"] = lawyer_info["name"]
            task["datetime"] = row["datetime"]
            task["description"] = row["description"]
            task["duration"] = row["duration"]
            task["amount"] = row["amount"]
            tasks.append(task)
        d_rows = cursor.execute("SELECT * FROM disbursements WHERE timesheet_id = ?", [id]).fetchall()
        disbursements = []
        for d_row in d_rows:
            disbursement = {}
            disbursement["description"] = d_row["description"]
            disbursement["amount"] = d_row["amount"]
            disbursements.append(disbursement)
        connection.close()
        return render_template("timesheet.html", timesheet=timesheet, client=client, tasks=tasks, disbursements=disbursements)
    else:
        flash("You are not authorised to view this timesheet!")
        return redirect(url_for("home"))

@app.route("/addtask/<id>", methods=["POST"])
@login_required
def addtask(id):
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    client_id = cursor.execute("SELECT * FROM timesheets WHERE id = ?", [id]).fetchone()["client_id"]
    rel = cursor.execute("SELECT * FROM users_clients WHERE user_id = ? AND client_id = ?", [user_id, client_id]).fetchall()
    if len(rel) != 0:
        lawyer_info = cursor.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
        data = request.get_json()
        date = data["date"]
        hours = round(float(data["hours"]), 1)
        description = data["description"]
        amount = hours * lawyer_info["rate"]
        cursor.execute("INSERT INTO tasks (user_id, client_id, timesheet_id, datetime, duration, description, amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [user_id, client_id, id, date, hours, description, amount])
        connection.commit()
        connection.close()
        return redirect(url_for("timesheet", id=id))
    else:
        flash("You are not authorised to add tasks to this timesheet!")
        return redirect(url_for("home"))

@app.route("/addtimesheet/<id>", methods=["POST"])
@login_required
def addtimesheet(id):
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    rel = cursor.execute("SELECT * FROM users_clients WHERE user_id = ? AND client_id = ?", [user_id, id]).fetchall()
    if len(rel) != 0:
        cursor.execute("INSERT INTO timesheets (client_id, status, created) VALUES (?, ?, ?)",
                    [id, 1, datetime.datetime.now().strftime("%d-%m-%Y")])
        in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [id]).fetchone()["in_progress"] + 1
        cursor.execute("UPDATE clients SET in_progress = ? WHERE id = ?", [in_progress, id])
        connection.commit()
        connection.close()
        return redirect(url_for("client", id=id))
    else:
        flash("You are not authorised to add timesheets for this client!")
        return redirect(url_for("home"))


@app.route("/disbursement/<id>", methods=["POST"])
@login_required
def disbursement(id):
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    client_id = cursor.execute("SELECT * FROM timesheets WHERE id = ?", [id]).fetchone()["client_id"]
    rel = cursor.execute("SELECT * FROM users_clients WHERE user_id = ? AND client_id = ?", [user_id, client_id]).fetchall()
    if len(rel) != 0:
        description = request.form.get("disbursement")
        amount = request.form.get("amount")
        cursor.execute("INSERT INTO disbursements (timesheet_id, description, amount) VALUES (?, ?, ?)", [id, description, amount])
        connection.commit()
        connection.close()
        return redirect(url_for('timesheet', id=id))
    else:
        flash("You are not authorised to add disbursements to this invoice!")
        return redirect(url_for("home"))

@app.route("/export/<id>", methods=["POST"])
@login_required
def export(id):
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    client_id = cursor.execute("SELECT * FROM timesheets WHERE id = ?", [id]).fetchone()["client_id"]
    rel = cursor.execute("SELECT * FROM users_clients WHERE user_id = ? AND client_id = ?", [user_id, client_id]).fetchall()
    if len(rel) != 0:
        filename = request.form.get("filename")
        file = filename + ".xlsx"
        cursor.execute("UPDATE timesheets SET status = 2 WHERE id = ?", [id])
        in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [client_id]).fetchone()["in_progress"] - 1
        payment_pending = cursor.execute("SELECT payment_pending FROM clients WHERE id = ?", [client_id]).fetchone()["payment_pending"] + 1
        cursor.execute("UPDATE clients SET in_progress = ?, payment_pending = ? WHERE id = ?", [in_progress, payment_pending, client_id])
        timesheet_query = "SELECT datetime, duration, description, amount FROM tasks WHERE client_id=:id"
        timesheet_dataframe = pandas.read_sql(timesheet_query, con=connection, params={"id": client_id})
        disbursement_query = "SELECT description, amount FROM disbursements WHERE timesheet_id=:id"
        disbursement_dataframe = pandas.read_sql(disbursement_query, con=connection, params={"id": id})
        invoice_dataframe = pandas.concat([timesheet_dataframe, disbursement_dataframe])
        invoice_dataframe.to_excel(file)
        connection.commit()
        connection.close()
        @app.after_request
        def after_export(response):
            if os.path.exists(file):
                os.remove(file)
            return response
        return send_file(file, mimetype='application/vnd.ms-excel')
    else:
        flash("You are not authorised to access this invoice!")
        return redirect(url_for("home"))
    
@app.route("/approve/<id>", methods=["POST"])
@login_required
def approve(id):
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    client_id = cursor.execute("SELECT * FROM timesheets WHERE id = ?", [id]).fetchone()["client_id"]
    rel = cursor.execute("SELECT * FROM users_clients WHERE user_id = ? AND client_id = ?", [user_id, client_id]).fetchall()
    if len(rel) != 0:
        cursor.execute("UPDATE timesheets SET status = 3 WHERE id = ?", [id])
        payment_pending = cursor.execute("SELECT payment_pending FROM clients WHERE id = ?", [client_id]).fetchone()["payment_pending"] - 1
        payment_received = cursor.execute("SELECT payment_received FROM clients WHERE id = ?", [client_id]).fetchone()["payment_received"] + 1
        cursor.execute("UPDATE clients SET payment_pending = ?, payment_received = ? WHERE id = ?", [payment_pending, payment_received, client_id])
        connection.commit()
        connection.close()
        return redirect(url_for('timesheet', id=id))
    else:
        flash("You are not authorised to approve this payment!")
        return redirect(url_for("home"))
    
@app.route("/import/<id>", methods=["POST"])
@login_required
def import_excel(id):
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    rel = cursor.execute("SELECT * FROM users_clients WHERE user_id = ? AND client_id = ?", [user_id, id]).fetchall()
    if len(rel) != 0:
        file = request.files['file']
        print(request.form.get("date"))
        date = datetime.datetime.strptime(request.form.get("date"), "%Y-%m-%d").strftime("%d-%m-%Y")
        status_code = request.form.get("status")
        cursor.execute("INSERT INTO timesheets (client_id, status, created) VALUES (?, ?, ?)",
                    [id, status_code, date])
        if status_code == 1:
            in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [id]).fetchone()["in_progress"] + 1
            cursor.execute("UPDATE clients SET in_progress = ? WHERE id = ?", [in_progress, id])
        elif status_code == 2:
            payment_pending = cursor.execute("SELECT payment_pending FROM clients WHERE id = ?", [id]).fetchone()["payment_pending"] + 1
            cursor.execute("UPDATE clients SET payment_pending = ? WHERE id = ?", [payment_pending, id])
        else:
            payment_received = cursor.execute("SELECT payment_received FROM clients WHERE id = ?", [id]).fetchone()["payment_received"] + 1
            cursor.execute("UPDATE clients SET payment_received = ? WHERE id = ?", [payment_received, id])
        timesheet_id = cursor.execute("SELECT id FROM timesheets WHERE created = ?", [date]).fetchone()["id"]
        tasks_dataframe = pandas.read_excel(file, sheet_name="Timesheet")
        for row in tasks_dataframe.to_dict("records"):
            task_lawyer = row["id"]
            task_datetime = row["datetime"]
            task_duration = row["duration"]
            task_description = row["description"]
            task_amount = row["amount"]
            cursor.execute("INSERT INTO tasks (user_id, client_id, timesheet_id, datetime, duration, description, amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           [task_lawyer, id, timesheet_id, task_datetime, task_duration, task_description, task_amount])
        disbursements_dataframe = pandas.read_excel(file, sheet_name="Disbursements")
        for row in disbursements_dataframe.to_dict("records"):
            disbursement_description = row["description"]
            disbursement_amount = row["amount"]
            cursor.execute("INSERT INTO disbursements (timesheet_id, description, amount) VALUES (?, ?, ?)",
                           [timesheet_id, disbursement_description, disbursement_amount])
        connection.commit()
        connection.close()
        return redirect(url_for("timesheet", id=timesheet_id))
    else:
        flash("You are not authorised to import timesheets for this client!")
        return redirect(url_for("home"))