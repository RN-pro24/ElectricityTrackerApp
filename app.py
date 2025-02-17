import os
import matplotlib.pyplot as plt
import base64
import numpy as np
import pandas as pd
import seaborn as sns
import helpers

from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from io import BytesIO


# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = 1

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configura la fecha
current_date = datetime.now().date()


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

#
@app.route("/", methods=["GET", "POST"])
def home():
    return render_template('index.html')



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    errors = {}

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            errors["username"] = "must provide username"

        # Ensure password was submitted
        elif not request.form.get("password"):
            errors["password"] = "must provide password",

        # Query database for username
        user_data = helpers.query_db(
            "SELECT * FROM users WHERE username = %s", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(user_data) != 1 or not check_password_hash(
            user_data[0]["hash"], request.form.get("password")
        ):
            errors["access"] = "invalid username and/or password"

        if errors:
            return render_template("login.html", errors=errors)

        # Remember which user has logged in
        session["user_id"] = user_data[0]["id"]

        # Redirect user to home page
        use = "This form, and others like it, let you customize where you want to record your money. Under 'asset,' choose an existing account or create a new one. It's the same for all categories. For example, use 'receivable' for pending income and 'savings' for, well, savings!"
        flash(use)
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", errors=errors)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


