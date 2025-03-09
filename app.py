import os
import matplotlib.pyplot as plt
import base64
import numpy as np
import pandas as pd
import seaborn as sns
import helpers

from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from io import BytesIO


# Configure application
app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["5 per minute", "30 per hour"]
)

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

#Home page
@app.route("/", methods=["GET", "POST"])
def home():
    return render_template('index.html')

#Register new user
@app.route("/register", methods=["GET","POST"])
def register():
    """"Register user"""

    session.clear()
    errors = {}

    if request.method == "POST":
        errors = helpers.validate_new_user_data(request.form)

        if not errors:
            #Get all user data
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            email = request.form.get("email")
            user_name = request.form.get("user_name")
            password= request.form.get("password")

            hashed_password = generate_password_hash(password)

            helpers.insert_db("INSERT INTO users(first_name, last_name, email, user_name, password) VALUES (%s,%s,%s,%s,%s)",
                               first_name, last_name, email, user_name,hashed_password
                              )
            
            user_data = helpers.query_db(
                    "SELECT * FROM users WHERE user_name = %s", user_name
                )
        
            session["user_id"] = user_data[0]["id"]
            flash("Registration successful")
            return redirect("/")
        
        else:
            return render_template("register.html", errors= errors)
    else:
        return render_template("register.html", errors={})


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        #Validate user entry
        errors, user_data = helpers.validate_user_data(request.form)

        #if not errors proceed with login
        if not errors:
            # Remember which user has logged in
            session["user_id"] = user_data[0]["id"]

            # Redirect user to home page
            use = "This module allows you to observe your currents metrics"
            flash(use)
            return redirect("/")

        #if errors, re-render login page with errors    
        else:
            return render_template("login.html", errors=errors)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", errors={})


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route('/modificar_plan', methods=['POST'])
def modificar_plan():
    plan = consultar_plan(request.form.get('select_plan'))
    return render_template('index.html', plan=plan, modal_to_open="edit")


