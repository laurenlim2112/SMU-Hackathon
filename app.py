from flask import Flask, flash, request, redirect, render_template, session, url_for, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

import sqlite3, os, pandas, datetime

app = Flask(__name__)
app.secret_key = os.urandom(12)

@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("home"))

@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    user = cursor.execute("SELECT name FROM users WHERE id = ?", [id]).fetchone()
    name = user["name"]
    clients = []
    rows = cursor.execute("SELECT * FROM users_clients WHERE user_id = ?", [id]).fetchall()
    tasks = cursor.execute("SELECT * FROM users_clients WHERE user_id = ?", [id]).fetchall()
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
    today = datetime.datetime.now().strftime("%d-%m-%Y")
    tasks = []
    t_rows = cursor.execute("SELECT * FROM tasks WHERE user_id = ? AND datetime = ?", [id, today]).fetchall()
    for row in t_rows:
        task = {}
        task["description"] = row["description"]
        task["duration"] = row["duration"]
        client_id = row["client_id"]
        task["client"] = cursor.execute("SELECT name FROM clients WHERE id = ?", [client_id]).fetchone()["name"]
        tasks.append(task)
    connection.close()
    return render_template("home.html", name=name, clients=clients, tasks=tasks, date=today)

@app.route("/register", methods=["GET", "POST"])
def register():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return render_template("register.html")
        email = request.form.get("email")
        if not email:
            return render_template("register.html")
        existing = cursor.execute("SELECT * FROM users WHERE email = ?", [email]).fetchall()
        if len(existing) > 0:
            return render_template("register.html")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password or not confirmation:
            return render_template("register.html")
        if password != confirmation:
            return render_template("register.html")
        hashed_password = generate_password_hash(password)
        rate = request.form.get("rate")
        firm_id = request.form.get("firm")
        cursor.execute("INSERT INTO users (name, email, hash, rate, firm) VALUES(?, ?, ?, ?, ?)", 
                        [name, email, hashed_password, rate, firm_id])
        connection.commit()
        connection.close()
        return redirect(url_for("home"))
    else:
        firm_rows = cursor.execute("SELECT * FROM firms").fetchall()
        firms = []
        for row in firm_rows:
            firm = {}
            firm["id"] = row["id"]
            firm["name"] = row["name"]
            firms.append(firm)
        return render_template("register.html", firms=firms)

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email:
            return render_template("login.html")
        elif not password:
            return render_template("login.html")
        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        result = cursor.execute("SELECT * FROM users WHERE email = ?", [email]).fetchall()
        if len(result) != 1 or not check_password_hash(result[0]["hash"], password):
            return render_template("login.html")
        session["user_id"] = result[0]["id"]
        connection.commit()
        connection.close()
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
    user_id = session["user_id"]
    name = request.form.get("name")
    email = request.form.get("email")
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    firm_id = cursor.execute("SELECT firm FROM users WHERE id = ?", [user_id]).fetchone()["firm"]
    result = cursor.execute("SELECT * FROM clients WHERE email = ? AND firm = ?", [email, firm_id]).fetchall()
    if len(result) > 0:
        return redirect(url_for("home"))
    cursor.execute("INSERT INTO clients (name, email, in_progress, payment_pending, payment_received, firm) VALUES (?, ?, ?, ?, ?, ?)", 
                   [name, email, 0, 0, 0, firm_id])
    client_id = cursor.execute("SELECT * FROM clients WHERE email = ?", [email]).fetchone()["id"]
    cursor.execute("INSERT INTO users_clients (user_id, client_id) VALUES (?, ?)", [user_id, client_id])
    connection.commit()
    connection.close()
    return redirect(url_for("home"))

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
        user_firm = cursor.execute("SELECT firm FROM users WHERE id = ?", [user_id]).fetchone()["firm"]
        new_lawyer_firm = cursor.execute("SELECT firm FROM users WHERE id = ?", [new_lawyer_id]).fetchone()["firm"]
        if user_firm != new_lawyer_firm:
            return redirect(url_for("home"))
        cursor.execute("INSERT INTO users_clients (user_id, client_id) VALUES (?, ?)", [new_lawyer_id, id])
        connection.commit()
        connection.close()
        return redirect(url_for("client", id=id))
    else:
        return redirect(url_for("home"))

@app.route("/clients/<id>", methods=["GET"])
@login_required
def client(id):
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    user_id = session["user_id"]
    user_firm = cursor.execute("SELECT firm FROM users WHERE id = ?", [user_id]).fetchone()["firm"]
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
            payment_pending_timesheet["invoice_generated"] = row["invoice_generated"]
            payment_pending_timesheets.append(payment_pending_timesheet)
        payment_received_rows = cursor.execute("SELECT * FROM timesheets WHERE client_id = ? AND status = 3", [client_info["id"]]).fetchall()
        payment_received_timesheets = []
        for row in payment_received_rows:
            payment_received_timesheet = {}
            payment_received_timesheet["id"] = row["id"]
            payment_received_timesheet["invoice_paid"] = row["invoice_paid"]
            payment_received_timesheets.append(payment_received_timesheet)
        lawyer_rows = cursor.execute("SELECT * FROM users WHERE firm = ?", [user_firm]).fetchall()
        lawyers = []
        for row in lawyer_rows:
            if row["id"] != user_id:
                lawyer = {}
                lawyer["id"] = row["id"]
                lawyer["name"] = row["name"]
                lawyers.append(lawyer)
        fixed_fee_rows = cursor.execute("SELECT * FROM fixed_fees WHERE firm = ?", [user_firm]).fetchall()
        fixed_fees = []
        for row in fixed_fee_rows:
            fixed_fee = {}
            fixed_fee["id"] = row["id"]
            fixed_fee["description"] = row["description"]
            fixed_fee["amount"] = row["amount"]
            fixed_fees.append(fixed_fee)
        connection.close()
        return render_template("client.html", client=client, 
                            in_progress_timesheets=in_progress_timesheets, 
                            payment_pending_timesheets=payment_pending_timesheets, 
                            payment_received_timesheets=payment_received_timesheets,
                            lawyers=lawyers,
                            fixed_fees = fixed_fees)
    else:
        return redirect(url_for("home"))

@app.route("/cases/<id>", methods=["GET"])
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
        tasks_total = cursor.execute("SELECT SUM(amount) FROM tasks WHERE timesheet_id = ?", [id]).fetchone()[0]
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
        d_total = cursor.execute("SELECT SUM(amount) FROM disbursements WHERE timesheet_id = ?", [id]).fetchone()[0]
        d_rows = cursor.execute("SELECT * FROM disbursements WHERE timesheet_id = ?", [id]).fetchall()
        disbursements = []
        for d_row in d_rows:
            disbursement = {}
            disbursement["description"] = d_row["description"]
            disbursement["amount"] = d_row["amount"]
            disbursements.append(disbursement)
        fixed_total = cursor.execute("SELECT SUM(amount) FROM fixed_fee_charges WHERE timesheet_id = ?", [id]).fetchone()[0]
        fixed_rows = cursor.execute("SELECT * FROM fixed_fee_charges WHERE timesheet_id = ?", [id]).fetchall()
        fixed_fees = []
        for fixed_row in fixed_rows:
            fixed_fee = {}
            fee_type = fixed_row["fixed_fee"]
            fixed_fee["description"] = cursor.execute("SELECT * FROM fixed_fees WHERE id = ?", [fee_type]).fetchone()["description"]
            fixed_fee["amount"] = fixed_row["amount"]
            fixed_fees.append(fixed_fee)
        invoice_total = 0
        if tasks_total:
            invoice_total += tasks_total
        if d_total:
            invoice_total += d_total
        if fixed_total:
            invoice_total += fixed_total
        connection.close()
        return render_template("timesheet.html", timesheet=timesheet, client=client, tasks=tasks, 
                               disbursements=disbursements, 
                               fixed_fees=fixed_fees,
                               tasks_total=tasks_total,
                               d_total=d_total,
                               fixed_total=fixed_total,
                               invoice_total=invoice_total)
    else:
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
        data = request.get_json()
        date = datetime.datetime.strptime(data["date"], "%d-%m-%Y").strftime("%d-%m-%Y")
        hours = round(float(data["hours"]), 1)
        description = data["description"]
        amount = hours * float(data["rate"])
        cursor.execute("INSERT INTO tasks (user_id, client_id, timesheet_id, datetime, duration, description, amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [user_id, client_id, id, date, hours, description, amount])
        connection.commit()
        connection.close()
        return redirect(url_for("timesheet", id=id))
    else:
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
        user_firm = cursor.execute("SELECT firm FROM users WHERE id = ?", [user_id]).fetchone()["firm"]
        cursor.execute("INSERT INTO timesheets (client_id, status, created, firm) VALUES (?, ?, ?, ?)",
                    [id, 1, datetime.datetime.now().strftime("%d-%m-%Y"), user_firm])
        in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [id]).fetchone()["in_progress"] + 1
        cursor.execute("UPDATE clients SET in_progress = ? WHERE id = ?", [in_progress, id])
        connection.commit()
        connection.close()
        return redirect(url_for("client", id=id))
    else:
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
        return redirect(url_for("home"))
    
@app.route("/billfixedfee/<id>", methods=["POST"])
@login_required
def billfixedfee(id):
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    rel = cursor.execute("SELECT * FROM users_clients WHERE user_id = ? AND client_id = ?", [user_id, id]).fetchall()
    if len(rel) != 0:
        upfront = int(request.form.get("upfront"))
        remainder = int(request.form.get("remainder"))
        if upfront + remainder != 100:
            return redirect(url_for('client', id=id))
        fee_id = request.form.get("fee")
        fee_description = cursor.execute("SELECT description FROM fixed_fees WHERE id = ?", [fee_id]).fetchone()["description"]
        addtotimesheet = request.form.get("addtotimesheet")
        user_firm = cursor.execute("SELECT firm FROM users WHERE id = ?", [user_id]).fetchone()["firm"]
        fee = cursor.execute("SELECT amount FROM fixed_fees WHERE id = ?", [fee_id]).fetchone()["amount"]
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        if remainder == 0:
            in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [id]).fetchone()["in_progress"] + 1
            cursor.execute("UPDATE clients SET in_progress = ? WHERE id = ?", [in_progress, id])
            cursor.execute("INSERT INTO timesheets (client_id, status, created, firm) VALUES (?, ?, ?, ?)", 
                           [id, 1, date, user_firm])
            timesheet_id = cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
            cursor.execute("INSERT INTO fixed_fee_charges (timesheet_id, fixed_fee, amount, datetime, description) VALUES (?, ?, ?, ?, ?)", 
                           [timesheet_id, fee_id, fee, date, fee_description])
        else:
            if remainder == 100:
                if addtotimesheet:
                    remaining_timesheet_id = request.form.get("timesheet")
                    cursor.execute("INSERT INTO fixed_fee_charges (timesheet_id, fixed_fee, amount, datetime, description) VALUES (?, ?, ?, ?, ?)", 
                                [remaining_timesheet_id, fee_id, fee, date, fee_description])
                else:
                    in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [id]).fetchone()["in_progress"] + 1
                    cursor.execute("UPDATE clients SET in_progress = ? WHERE id = ?", [in_progress, id])
                    cursor.execute("INSERT INTO timesheets (client_id, status, created, firm) VALUES (?, ?, ?, ?)", 
                                [id, 1, date, user_firm])
                    remaining_timesheet_id = cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
                    cursor.execute("INSERT INTO fixed_fee_charges (timesheet_id, fixed_fee, amount, datetime, description) VALUES (?, ?, ?, ?, ?)", 
                                   [remaining_timesheet_id, fee_id, fee, date, fee_description])
            else:
                upfront_fee = round((upfront * fee) / 100, 2)
                remaining_fee = fee - upfront_fee
                if addtotimesheet:
                    in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [id]).fetchone()["in_progress"] + 1
                    cursor.execute("UPDATE clients SET in_progress = ? WHERE id = ?", [in_progress, id])
                    cursor.execute("INSERT INTO timesheets (client_id, status, created, firm) VALUES (?, ?, ?, ?)", 
                                [id, 1, date, user_firm])
                    upfront_timesheet_id = cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
                    remaining_timesheet_id = request.form.get("timesheet")
                    cursor.execute("INSERT INTO fixed_fee_charges (timesheet_id, fixed_fee, amount, datetime, description) VALUES (?, ?, ?, ?, ?)", 
                                [upfront_timesheet_id, fee_id, upfront_fee, date, fee_description])
                    cursor.execute("INSERT INTO fixed_fee_charges (timesheet_id, fixed_fee, amount, datetime, description) VALUES (?, ?, ?, ?, ?)", 
                                [remaining_timesheet_id, fee_id, remaining_fee, date, fee_description])
                else:
                    in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [id]).fetchone()["in_progress"] + 2
                    cursor.execute("UPDATE clients SET in_progress = ? WHERE id = ?", [in_progress, id])
                    cursor.execute("INSERT INTO timesheets (client_id, status, created, firm) VALUES (?, ?, ?, ?)", 
                                [id, 1, date, user_firm])
                    upfront_timesheet_id = cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
                    cursor.execute("INSERT INTO timesheets (client_id, status, created, firm) VALUES (?, ?, ?, ?)", 
                                [id, 1, date, user_firm])
                    remaining_timesheet_id = cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
                    cursor.execute("INSERT INTO fixed_fee_charges (timesheet_id, fixed_fee, amount, datetime, description) VALUES (?, ?, ?, ?, ?)", 
                                   [upfront_timesheet_id, fee_id, upfront_fee, date, fee_description])
                    cursor.execute("INSERT INTO fixed_fee_charges (timesheet_id, fixed_fee, amount, datetime, description) VALUES (?, ?, ?, ?, ?)", 
                                   [remaining_timesheet_id, fee_id, remaining_fee, date, fee_description])
        connection.commit()
        connection.close()
        return redirect(url_for('client', id=id))
    else:
        return redirect(url_for("home"))
    
@app.route("/newfixedfee", methods=["POST"])
@login_required
def newfixedfee():
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    description = request.form.get("description")
    amount = request.form.get("amount")
    user_firm = cursor.execute("SELECT firm FROM users WHERE id = ?", [user_id]).fetchone()["firm"]
    existing = cursor.execute("SELECT * FROM fixed_fees WHERE description = ? AND firm = ?", [description, user_firm]).fetchall()
    if len(existing) != 0:
        return redirect(url_for("home"))
    cursor.execute("INSERT INTO fixed_fees (description, amount, firm) VALUES (?, ?, ?)", [description, amount, user_firm])
    connection.commit()
    connection.close()
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
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        filename = request.form.get("filename")
        file = filename + ".xlsx"
        cursor.execute("UPDATE timesheets SET status = 2, invoice_generated = ? WHERE id = ?", [date, id])
        in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [client_id]).fetchone()["in_progress"] - 1
        payment_pending = cursor.execute("SELECT payment_pending FROM clients WHERE id = ?", [client_id]).fetchone()["payment_pending"] + 1
        cursor.execute("UPDATE clients SET in_progress = ?, payment_pending = ? WHERE id = ?", [in_progress, payment_pending, client_id])
        fixed_fees_query = "SELECT datetime, description, amount FROM fixed_fee_charges WHERE timesheet_id=:id"
        fixed_fees_dataframe = pandas.read_sql(fixed_fees_query, con=connection, params={"id": id})
        timesheet_query = "SELECT datetime, duration, description, amount FROM tasks WHERE timesheet_id=:id"
        timesheet_dataframe = pandas.read_sql(timesheet_query, con=connection, params={"id": id})
        disbursement_query = "SELECT description, amount FROM disbursements WHERE timesheet_id=:id"
        disbursement_dataframe = pandas.read_sql(disbursement_query, con=connection, params={"id": id})
        invoice_dataframe = pandas.concat([fixed_fees_dataframe, timesheet_dataframe, disbursement_dataframe])
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
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        cursor.execute("UPDATE timesheets SET status = 3, invoice_paid = ? WHERE id = ?", [date, id])
        payment_pending = cursor.execute("SELECT payment_pending FROM clients WHERE id = ?", [client_id]).fetchone()["payment_pending"] - 1
        payment_received = cursor.execute("SELECT payment_received FROM clients WHERE id = ?", [client_id]).fetchone()["payment_received"] + 1
        cursor.execute("UPDATE clients SET payment_pending = ?, payment_received = ? WHERE id = ?", [payment_pending, payment_received, client_id])
        connection.commit()
        connection.close()
        return redirect(url_for('timesheet', id=id))
    else:
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
        user_firm = cursor.execute("SELECT firm FROM users WHERE id = ?", [user_id]).fetchone()["firm"]
        file = request.files['file']
        date = datetime.datetime.strptime(request.form.get("date"), "%Y-%m-%d").strftime("%d-%m-%Y")
        status_code = request.form.get("status")
        in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [id]).fetchone()["in_progress"] + 1
        cursor.execute("UPDATE clients SET in_progress = ? WHERE id = ?", [in_progress, id])
        cursor.execute("INSERT INTO timesheets (client_id, status, created, firm) VALUES (?, ?, ?, ?)",
                    [id, status_code, date, user_firm])
        timesheet_id = cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
        if status_code == 1:
            in_progress = cursor.execute("SELECT in_progress FROM clients WHERE id = ?", [id]).fetchone()["in_progress"] + 1
            cursor.execute("UPDATE clients SET in_progress = ? WHERE id = ?", [in_progress, id])
        elif status_code == 2:
            payment_pending = cursor.execute("SELECT payment_pending FROM clients WHERE id = ?", [id]).fetchone()["payment_pending"] + 1
            cursor.execute("UPDATE clients SET payment_pending = ? WHERE id = ?", [payment_pending, id])
        else:
            payment_received = cursor.execute("SELECT payment_received FROM clients WHERE id = ?", [id]).fetchone()["payment_received"] + 1
            cursor.execute("UPDATE clients SET payment_received = ? WHERE id = ?", [payment_received, id])
        tasks_dataframe = pandas.read_excel(file, sheet_name="Timesheet")
        for row in tasks_dataframe.to_dict("records"):
            task_lawyer = cursor.execute("SELECT id FROM users WHERE name = ? AND firm = ?", [row["lawyer"], user_firm]).fetchone()["id"]
            task_datetime = row["datetime"].to_pydatetime().strftime("%d-%m-%Y")
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
        fixed_fees_dataframe = pandas.read_excel(file, sheet_name="Fixed Fees")
        for row in fixed_fees_dataframe.to_dict("records"):
            fixed_fee_datetime = row["datetime"].to_pydatetime().strftime("%d-%m-%Y")
            fixed_fee_description = row["description"]
            fixed_fee = cursor.execute("SELECT id FROM fixed_fees WHERE firm = ? AND description = ?", 
                                       [user_firm, fixed_fee_description]).fetchone()["id"]
            fixed_fee_amount = row["amount"]
            cursor.execute("INSERT INTO fixed_fee_charges (timesheet_id, fixed_fee, amount, datetime, description) VALUES (?, ?, ?, ?, ?)",
                           [timesheet_id, fixed_fee, fixed_fee_amount, fixed_fee_datetime, fixed_fee_description])
        connection.commit()
        connection.close()
        return redirect(url_for("timesheet", id=timesheet_id))
    else:
        return redirect(url_for("home"))