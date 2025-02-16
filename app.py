import os
import matplotlib.pyplot as plt
import base64
import numpy as np
import pandas as pd
import seaborn as sns
import mysql.connector

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

# Configure MySQL database
mydb = mysql.connector.connect(
  host="localhost",
  user="admin_user",
  password="Isa240122-*",
  database="electricity_tracker_app"
)

mycursor = mydb.cursor()

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


