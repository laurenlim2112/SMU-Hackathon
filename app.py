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
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Name cannot be left blank!")
        email = request.form.get("email")
        if not email:
            flash("Email cannot be left blank!")
        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL, email TEXT NOT NULL, hash BLOB NOT NULL)")
        existing = cursor.execute("SELECT * FROM users WHERE email = ?", [email])
        if existing:
            flash("Email already in use!")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password or not confirmation:
            flash("Password and confirmation cannot be left blank!")
        if password != confirmation:
            flash("Passwords do not match!")
        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (name, email, hash) VALUES(?, ?, ?)", [name, email, hashed_password])
        # db.execute("CREATE TABLE IF NOT EXISTS ")
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
        elif not password:
            flash("No password")
        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        result = cursor.execute("SELECT * FROM users WHERE email = ?", [email]).fetchall()
        if len(result) != 1 or not check_password_hash(result[0]["hash"], password):
            flash("Invalid email address and/or password")
        session["user_id"] = result[0]["id"]
        flash("Login successful!")
        return redirect("/")
    else:
        return render_template("login.html")
    
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")