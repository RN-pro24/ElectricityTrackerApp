import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

#Conect with mySQL database
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="admin_user",
        password="Isa240122-*",
        database="electricity_tracker_app"
    )

#make query in database
def query_db(query, parameters=None):
    mydb = connect_db()
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute(query, parameters)
    results = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return results

#insert data en database
def insert_db(query, data):
    mydb = connect_db()
    mycursor = mydb.cursor()
    mycursor.execute(query, data)
    mydb.commit()
    mycursor.close()
    mydb.close()

#Validation for new users

def validate_new_user_data(form_data):

    #Create dictionary for errors
    errors = {}

    #Validate all the input entry
    if not form_data.get("first_name"):
        errors["first_name"] = "Must provide first name"
    if not form_data.get("last_name"):
        errors["last_name"] = "Must provide last name"
    if not form_data.get("email"):
        errors["email"] = "Must provide email"
    if not form_data.get("user_name"):
        errors["user_name"] = "Must provide username"
    if not form_data.get("password"):
        errors["password"] = "Must provide password"
    if not form_data.get("confirmation"):
        errors["confirmation"] = "Must confirm password"
    
    if errors:
        return errors
    
    #Validate username and passwords

    request_user = form_data.get("user_name")
    try:
        if query_db("SELECT * FROM users WHERE user_name = %s", (request_user,)):
            errors["user_exist"] = "The username exists"
    except Exception as e:
            errors["database_error"] = f"An error occurred: {e}"
    
    if form_data.get("password") != form_data.get("confirmation"):
        errors["match"] = "passwords don't macht"
    
    return errors if errors else None

def validate_user_data(form_data):
    
    #Create dictionary for errors
    errors = {}
        
    # Ensure username and password was submitted
    if not form_data.get("username"):
        errors["username"] = "must provide username"
    if not form_data.get("password"):
        errors["password"] = "must provide password"
    
    if errors:
        return errors, None
    
    # Query database for username
    user_data = query_db(
        "SELECT * FROM users WHERE user_name = %s", (form_data.get("username"),)
    )

    # Ensure username exists and password is correct
    if len(user_data) != 1 or not check_password_hash(
        user_data[0]["password"], form_data.get("password")
    ):
        errors["access"] = "invalid username and/or password"
        return errors, None
    
    else:
        return errors, user_data

def validate_energy_cost_register(form_data, user, type_validate, fee_id=None):
    errors = {}

    #Comprueba la existencia de la fecha y la validez de la fecha
    if not form_data.get("date"):
        errors["date"] = "Must provide date"
    try:
        date_object = datetime.strptime(form_data.get("date"), "%Y-%m-%d").date()
    except ValueError:
            errors["invalid_date"] = "Must provide valid date"

    #Comprueba el pais
    if not form_data.get("country"):
        errors["country"] = "Must provide country"
    #Comprueba la compañia
    if not form_data.get("company"):
        errors["company"] = "Must provide company"
    #Comprueba la existencia del contrato
    if not form_data.get("contract_electrical"):
        errors["contract_electrical"] = "Must provide contract electrical"
    #Comprueba la existencia del tipo de fee
    if not form_data.get("fee_type"):
        errors["fee_type"] = "Must provide fee type"
    #Comprueba la existencia del nombre
    if not form_data.get("fee_name"):
        errors["fee_name"] = "Must provide fee name"
    #Comprueba la hora inicial del plan
    if not form_data.get("start_time"):
        errors["start_time"] = "Must provide start time"
    #comprueba la hora final del plan
    if not form_data.get("end_time"):
        errors["end_time"] = "Must provide end time"
    #Comprueba el precio por kwh
    if not form_data.get("price_per_kWh"):
        errors["price"] = "Must provide price_per_kWh"
    #Comprueba que el precio este en el margen correcto
    try:
        amount = float(form_data.get("price_per_kWh"))
    except ValueError:
        errors["errors.price_not_number"] = "Is not a number"
    #Comprueba el estatus
    if not form_data.get("status"):
        errors["status"] = "Must provide status active or inactive"

    if form_data.get("status") not in ["Active", "Inactive"]:
        errors["status_not_valid"] = "Must provide status active or inactive"

    
    #Si existen errores los envia
    if errors:
        return errors

    #Si es el registro inicial entonces valida que no este repetido    
    if type_validate == "register":

        try:
            query_fee_name = form_data.get("fee_name")
            query_fee_name = query_fee_name.strip()
            if query_db( "SELECT fee_name FROM energetic_cost WHERE user_id = %s AND fee_name = %s",
                        (user, query_fee_name)
                        ):
                errors["fee_name_exist"] = "Fee name already exist"

        except Exception as e:
                errors["database_error"] = f"An error occurred: {e}"
    
    #Si es edicion del plan, este proceso confirma que es el mismo nombre del plan
    if type_validate == "edit":
        actually_fee_name = query_db("SELECT fee_name FROM energetic_cost WHERE user_id = %s AND id = %s", (fee_id, user))
        if actually_fee_name and actually_fee_name[0]["fee_name"] != form_data.get("fee_name"):
            errors["fee_name"] = "The name must not be changed"

    return errors if errors else None

def update_energy_cost_values(user, form_data):
    errors = {}

    query = """
    UPDATE energetic_cost
    SET
        country = %s,
        date = %s,
        company = %s,
        contract_electrical = %s,
        fee_type = %s,
        start_time = %s,
        end_time = %s,
        price_per_kWh = %s,
        modified = %s,
        status = %s
    WHERE
        user_id = %s 
    AND
        fee_name = %s
    """

    values = (form_data.get("country"),form_data.get("date"),form_data.get("company"), form_data.get("contract_electrical"),
              form_data.get("fee_type"),form_data.get("start_time"),form_data.get("end_time"),form_data.get("price_per_kWh"),
              datetime.now(), user, form_data.get("fee_name"), form_data.get("status"))

    try:
        insert_db(query,values)

    except Exception as e:
        errors["database_error"] = f"An error occurred: {e}"
    
    return errors if errors else None

def register_energy_cost_values(user, form_data):
    errors = {}

    query = """
    INSERT INTO energetic_cost
    (
        user_id,
        country,
        date,
        company,
        contract_electrical,
        fee_type,
        fee_name,
        start_time,
        end_time,
        price_per_kWh,
        modified,
        status
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    values = (user, form_data.get("country"),form_data.get("date"),form_data.get("company"), form_data.get("contract_electrical"),
              form_data.get("fee_type"), form_data.get("fee_name"), form_data.get("start_time"),form_data.get("end_time"),form_data.get("price_per_kWh"),
              datetime.now(), form_data.get("status"))

    try:
        print("ant queryy")
        insert_db(query,values)
        print("listo")

    except Exception as e:
        errors["database_error"] = f"An error occurred: {e}"
    
    return errors if errors else True