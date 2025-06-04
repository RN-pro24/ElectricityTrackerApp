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


"""Manejos de usuarios"""

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
                               (first_name, last_name, email, user_name,hashed_password)
                              )
            
            user_data = helpers.query_db(
                    "SELECT * FROM users WHERE user_name = %s", (user_name,)
                )
        
            session["user_id"] = user_data[0]["id"]
            flash("Registration successful")
            return redirect("/")
        
        else:
            return render_template("register.html", errors= errors)
    else:
        return render_template("register.html", errors= {})


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


"""Creacion y desarrollo de planes"""


@app.route('/plans', methods=['GET'])
def view_all_plans():

    plans = helpers.query_db("SELECT * FROM energetic_cost WHERE user_id = %s", (session["user_id"],))

    #Si existe el plan lo envia
    if plans:
        return render_template('energy_cost.html', plans=plans, errors={}, plan=None)
    
    #Si no existe lo envia al modal de registro
    else:
        flash("You don't have plans, please register one")
        return render_template('energy_cost.html', plans=[], modal_to_open="modalRegistrar", errors={}, plan=None)


@app.route('/select_plan', methods=['GET','POST'])
def select_plan():

    plans = helpers.query_db("SELECT * FROM energetic_cost WHERE user_id = %s", (session["user_id"],))

    if request.method == "GET":

        if plans:
            flash("Select plan to modify")
            return render_template('energy_cost.html', plans=plans, errors={} ,modal_to_open="modalModificar", plan=None)
        
        else:
            flash("You don't have plans, please register one")
            return render_template('energy_cost.html', plans=[], errors={} , modal_to_open="modalRegistrar", plan=None)
    
    if request.method == "POST":
        errors= {}
        select_plan = request.form.get("select_plan")
        
        if plans:    
            if not select_plan or not any(plan["fee_name"] == select_plan for plan in plans):
                errors["select_plan"] = "The plan is missing or does not exist"
                flash("Please try again")
                return render_template('energy_cost.html',errors=errors , plans=plans, modal_to_open="modalModificar", plan=None)
            
            plan = next((plan for plan in plans if plan["fee_name"] == select_plan), None)
            return render_template('energy_cost.html', plan=plan, errors={} , modal_to_open="modal_edit_plan")
            
                
        else:
            flash("You don't have plans, please register one")
            return render_template('energy_cost.html', plans=[], errors={} ,modal_to_open="modalRegistrar", plan=None)
        
@app.route('/edit_plan', methods=['GET','POST'])
def edit_plan():
    #Declarar variable para uso de ambos metodos
    fee_id = None
    fee_name = ""
    
    #Si el usuario envia el formulario

    if request.method == "POST":

        #Se detectan errores en caso de existir        
        errors = helpers.validate_energy_cost_register(request.form, session["user_id"], "edit", fee_id)

        #Si no existen errores intenta actualizar la informacion
        if not errors:
            try:
                if helpers.update_energy_cost_values(session["user_id"], request.form):
                    #Notifica la actualizacion y regresa a la pantalla inicial
                    flash("Update complete")
                    return redirect('/plans') 
                    #return render_template('energy_cost.html', plans=[], errors={} , plan=None)

            #Si se obtiene un error lo capta 
            except Exception as e:
                errors["database_error"] = f"An error occurred: {e}"
            
            #Si existe un error envia el error de lo contrario renderiza la pantalla con
            if errors:
                return render_template('energy_cost.html', plan=request.form, errors=errors , modal_to_open="modal_edit_plan")

        else:
            return render_template('energy_cost.html', plan=request.form, errors=errors , modal_to_open="modal_edit_plan")
    
    #Si el metodo es GET entonces asigna fee_name y fee_id
    else:

        fee_name = request.form.get("fee_name")
        fee_id = helpers.query_db("SELECT id FROM energetic_cost WHERE fee_name = %s", (fee_name,))

@app.route('/register_plan' , methods=['GET','POST'])
def register_plan():

    errors = {}
    
    if request.method == "POST":
        errors = helpers.validate_energy_cost_register(request.form, session['user_id'],"register")

        if not errors:

            try:
                if helpers.register_energy_cost_values(session['user_id'], request.form):
                    flash("Register Complete")
                    return render_template('energy_cost.html', plans=[], errors={} , plan=None)
                else:
                    errors["registration_failed"] = "Unable to complete registration."

            except Exception as e:
                errors["database_error"] = f"An error occurred: {e}"
            
        return render_template('energy_cost.html', errors=errors, modal_to_open="modalRegistrar")

    else:
        return render_template('energy_cost.html', errors={})
    

"""Creacion y desarrollo de gadgets"""

@app.route('/gadgets', methods=['GET'])
def view_all_gadgets():

    gadgets = helpers.query_db("SELECT * FROM gadgets WHERE user_id = %s", (session["user_id"],))

    #Si existe el gadget lo envia
    if gadgets:
        return render_template('gadgets.html', gadgets=gadgets, errors={}, gadget=None)
    
    #Si no existe lo envia al modal de registro
    else:
        flash("You don't have gadgets, please register one")
        return render_template('gadgets.html', gadgets=[], modal_to_open="registrar_gadget", errors={}, gadget=None)

@app.route('/select_gadget', methods=['GET','POST'])
def select_gadget():

    gadgets = helpers.query_db("SELECT * FROM gadgets WHERE user_id = %s", (session["user_id"],))

    if request.method == "GET":

        if gadgets:
            flash("Select gadget to modify")
            return render_template('gadgets.html', gadgets=gadgets, errors={}, modal_to_open="modal_edit_gadget", gadget=None)
        
        else:
            flash("You don't have gadget, please register one")
            return render_template('gadgets.html', gadgets=[], errors={} , modal_to_open="registrar_gadget", plan=None)
    
    if request.method == "POST":
        errors= {}
        select_gadget = request.form.get("select_gadget")
        
        if gadgets:
            if not select_gadget or not any(gadget["gadget_name"] == select_gadget for gadget in gadgets):
                errors["select_gadget"] = "The gadget is missing or does not exist"
                flash("Please try again")
                return render_template('gadgets.html',errors=errors , gadgets=gadgets, modal_to_open="modal_edit_gadget", gadget=None)
            
            gadget = next((gadget for gadget in gadgets if gadget["gadget_name"] == select_plan), None)
            return render_template('gadgets.html', gadgets=gadgets, errors={} , modal_to_open="modal_edit_gadget")
            
                
        else:
            flash("You don't have gadgets, please register one")
            return render_template('gadgets.html', gadgets=[], errors={} ,modal_to_open="registrar_gadget", plan=None)
        
"""@app.route('/edit_plan', methods=['GET','POST'])
def edit_plan():
    #Declarar variable para uso de ambos metodos
    fee_id = None
    fee_name = ""
    
    #Si el usuario envia el formulario

    if request.method == "POST":

        #Se detectan errores en caso de existir        
        errors = helpers.validate_energy_cost_register(request.form, session["user_id"], "edit", fee_id)

        #Si no existen errores intenta actualizar la informacion
        if not errors:
            try:
                if helpers.update_energy_cost_values(session["user_id"], request.form):
                    #Notifica la actualizacion y regresa a la pantalla inicial
                    flash("Update complete")
                    return redirect('/plans') 
                    #return render_template('energy_cost.html', plans=[], errors={} , plan=None)

            #Si se obtiene un error lo capta 
            except Exception as e:
                errors["database_error"] = f"An error occurred: {e}"
            
            #Si existe un error envia el error de lo contrario renderiza la pantalla con
            if errors:
                return render_template('energy_cost.html', plan=request.form, errors=errors , modal_to_open="modal_edit_plan")

        else:
            return render_template('energy_cost.html', plan=request.form, errors=errors , modal_to_open="modal_edit_plan")
    
    #Si el metodo es GET entonces asigna fee_name y fee_id
    else:

        fee_name = request.form.get("fee_name")
        fee_id = helpers.query_db("SELECT id FROM energetic_cost WHERE fee_name = %s", (fee_name,))"""