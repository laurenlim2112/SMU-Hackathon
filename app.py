from flask import Flask, flash, request, redirect, render_template, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

import sqlite3
import os

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
        cursor.execute("INSERT INTO users (name, email, hash) VALUES(?, ?, ?)", [name, email, hashed_password])
        connection.commit()
        connection.close()
        flash("Registration successful!")
        return redirect("/")
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
        connection.close()
        flash("Login successful!")
        return redirect("/")
    else:
        return render_template("login.html")
    
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")

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
        return redirect("/")
    cursor.execute("INSERT INTO clients (name, email, status) VALUES(?, ?, ?)", [name, email, 0])
    user_id = session["user_id"]
    client_id = cursor.execute("SELECT * FROM clients WHERE email = ?", [email]).fetchone()["id"]
    cursor.execute("INSERT INTO users_clients (user_id, client_id) VALUES (?, ?)", [user_id, client_id])
    connection.commit()
    connection.close()
    flash("Client added successfully!")
    return redirect("/")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    user = cursor.execute("SELECT name FROM users WHERE id = ?", [user_id]).fetchone()
    name = user["name"]
    clients = []
    rows = cursor.execute("SELECT * FROM users_clients WHERE user_id = ?", [user_id]).fetchall()
    for row in rows:
        client_id = row["client_id"]
        client_info = cursor.execute("SELECT * FROM clients WHERE id = ?", [client_id]).fetchone()
        client = {}
        client["name"] = client_info["name"]
        client["email"] = client_info["email"]
        client["status"] = client_info["status"]
        clients.append(client)
    connection.close()
    return render_template("dashboard.html", name=name, clients=clients)