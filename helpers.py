import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from datetime import date


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
    try:
        mydb = connect_db()
        mycursor = mydb.cursor()
        mycursor.execute(query, data)
        mydb.commit()
        mycursor.close()
        mydb.close()
        return True
    
    except Exception as e:
        print(f"Database error: {e}")

        return None


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
              datetime.now(), form_data.get("status"), user, form_data.get("fee_name"))

    if insert_db(query,values):
        return True
    else:
        return None

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
        insert_db(query,values)

    except Exception as e:
        errors["database_error"] = f"An error occurred: {e}"
    
    return errors if errors else True


def validate_gadget_register(form_data, user, type_validate, gadget_id=None):
    errors = {}

    #Comprueba la existencia de la fecha y la validez de la fecha
    if not form_data.get("date"):
        errors["date"] = "Must provide date"
    try:
        date_object = datetime.strptime(form_data.get("date"), "%Y-%m-%d").date()
    except ValueError:
            errors["invalid_date"] = "Must provide valid date"

    #Comprueba watts
    if not form_data.get("watts"):
        errors["watts"] = "Must provide Watts"
    #Comprueba que watts sea numero
    try:
        amount = float(form_data.get("watts"))
    except ValueError:
        errors["watts"] = "Watts is not a number"

    #Comprueba kWh
    if not form_data.get("kWh"):
        errors["kWh"] = "Must provide kWh"
    #Comprueba que kWh sea numero
    try:
        amount = float(form_data.get("kWh"))
    except ValueError:
        errors["kWh"] = "kWh is not a number"

    #Comprueba la existencia del tipo de precio
    if not form_data.get("price_type"):
        errors["price_type"] = "Must provide price type"
    #Comprueba la existencia del tiempo de uso
    if not form_data.get("hours_usage"):
        errors["hours_usage"] = "Must provide hour usage"
    #Comprueba la existencia de la eficiencia
    electrical_efficiency= form_data.get("electrical_efficiency")
    if not electrical_efficiency or len(electrical_efficiency)>5:
        errors["electrical_efficiency"] = "Must provide correct electrical efficiency"
    #Comprueba el tipo de gadget
    if not form_data.get("gadget_type"):
        errors["gadget_type"] = "Must provide gadget type"
    #comprueba ubicacion 
    if not form_data.get("house_location"):
        errors["house_location"] = "Must provide house location"
    
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
            query_gadget_name = form_data.get("gadget_name")
            query_gadget_name = query_gadget_name.strip()
            if query_db( "SELECT gadget_name FROM gadgets WHERE user_id = %s AND gadget_name = %s",
                        (user, query_gadget_name)
                        ):
                errors["gadget_name"] = "Gadget name already exist"

        except Exception as e:
                errors["database_error"] = f"An error occurred: {e}"
    
    #Si es edicion del gadget, este proceso confirma que es el mismo nombre del gadget
    if type_validate == "edit":
        actually_gadget_name = query_db("SELECT gadget_name FROM gadgets WHERE user_id = %s AND id = %s", (gadget_id, user))
        if actually_gadget_name and actually_gadget_name[0]["gadget_name"] != form_data.get("gadget_name"):
            errors["gadget_name"] = "The name must not be changed"

    return errors if errors else None

def update_gadget_values(user, form_data):
    errors = {}

    query = """
    UPDATE gadgets
    SET
        watts = %s,
        kWh = %s,
        price_type = %s,
        hours_usage = %s,
        electrical_efficiency = %s,
        gadget_type = %s,
        house_location = %s,
        status = %s,
        date = %s,
        energetic_cost_id = %s
    WHERE
        user_id = %s 
    AND
        gadget_name = %s
    """
    #Date en este caso es para modificaciones
    price_type_id = query_db("SELECT id FROM energetic_cost WHERE user_id = %s AND fee_name = %s", user,form_data.get("price_type"))
    values = (form_data.get("watts"),form_data.get("kWh"),form_data.get("price_type"), form_data.get("hours_usage"),
              form_data.get("electrical_efficiency"),form_data.get("gadget_type"),form_data.get("house_location"),form_data.get("status"),
              datetime.now(),price_type_id[0]["id"],user,form_data.get("gadget_name"))

    if insert_db(query,values):
        return True
    else:
        return None
    
def register_gadgets_values(user, form_data):
    errors = {}

    query = """
    INSERT INTO gadgets
    (
        user_id,
        gadget_name,
        watts,
        kWh,
        price_type,
        hours_usage,
        electrical_efficiency,
        gadget_type,
        house_location,
        status,
        energetic_cost_id,
        date
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    price_type_id = query_db("SELECT id FROM energetic_cost WHERE user_id = %s AND fee_name = %s", (user,form_data.get("price_type")))
    values = (user, form_data.get("gadget_name"),form_data.get("watts"),form_data.get("kWh"), form_data.get("price_type"),
              form_data.get("hours_usage"), form_data.get("electrical_efficiency"), form_data.get("gadget_type"),form_data.get("house_location"),form_data.get("status"),
              price_type_id[0]["id"], form_data.get("date"))

    try:
        insert_db(query,values)

    except Exception as e:
        errors["database_error"] = f"An error occurred: {e}"
    
    return errors if errors else True


def validate_bill_register(form_data, user):
    errors = {}

    #Comprueba la existencia de la fecha y la validez de la fecha
    if not form_data.get("date"):
        errors["date"] = "Must provide date"
    try:
        date_object = datetime.strptime(form_data.get("date"), "%Y-%m-%d").date()
    except ValueError:
            errors["invalid_date"] = "Must provide valid date"

    #Comprueba bill month
    if not form_data.get("bill_month"):
        errors["bill_month"] = "Must provide bill month"

    #Comprueba bill number
    if not form_data.get("bill_number"):
        errors["bill_number"] = "Must provide bill number"
    try:
        amount = float(form_data.get("bill_number"))
    except ValueError:
        errors["bill_number"] = "bill number consumption is not a number"
  
    #Comprueba kwh consumption
    if not form_data.get("kWh_consumption"):
        errors["kWh_consumption"] = "Must provide kWh consumption"
    #Comprueba que kWh sea numero
    try:
        amount = float(form_data.get("kWh_consumption"))
    except ValueError:
        errors["kWh_consumption"] = "kWh consumption is not a number"

    #Comprueba net bill
    if not form_data.get("net_bill"):
        errors["net_bill"] = "Must provide net bill"
    #Comprueba que net bill sea numero
    try:
        amount = float(form_data.get("net_bill"))
    except ValueError:
        errors["net_bill"] = "Net bill is not a number"

    #Comprueba net bill
    if not form_data.get("kWh_price"):
        errors["kWh_price"] = "Must provide kWh price"
    #Comprueba que net bill sea numero
    try:
        amount = float(form_data.get("kWh_price"))
    except ValueError:
        errors["kWh_price"] = "kWh price is not a number"

        
    #Si existen errores los envia
    if errors:
        return errors

def register_bill(user, form_data):
    errors = {}

    query = """
    INSERT INTO history_consumption_bill
    (
        user_id,
        bill_date,
        bill_number,
        bill_month,
        kWh_consumption,
        net_bill,
        kWh_price
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    
    values = (user, form_data.get("date"),form_data.get("bill_number"),form_data.get("bill_month"), form_data.get("kWh_consumption"),
              form_data.get("net_bill"), form_data.get("kWh_price"))

    try:
        insert_db(query,values)

    except Exception as e:
        errors["database_error"] = f"An error occurred: {e}"
    
    return errors if errors else True

def validate_bill_dates(form_data, user):
    errors = {}

    def parse_date(field_name):
        value = form_data.get(field_name)
        if not value:
            errors[field_name] = "Must provide date"
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            errors[field_name] = "Must provide valid date"
            return None

    # Parse dates
    date_1 = parse_date("date_1")
    date_2 = parse_date("date_2")
    date_3 = parse_date("date_3")
    date_4 = parse_date("date_4")  

    if errors:
        return errors

    # Validar existencia en la base de datos
    for field_name, date_value in [("date_1", date_1), ("date_2", date_2), ("date_3", date_3), ("date_4", date_4)]:
        result = query_db(
            "SELECT id FROM history_consumption_bill WHERE user_id = %s AND bill_date = %s",
            user, date_value
        )
        if not result:
            errors[field_name] = f"{field_name.replace('_', ' ').title()} does not exist in records"

    # Validar orden lógico
    if date_1 and date_2 and date_1 > date_2:
        errors["date_1"] = "First period: Start date must be earlier than end date"
    if date_3 and date_4 and date_3 > date_4:
        errors["date_3"] = "Second period: Start date must be earlier than end date"

    return errors if errors else None

    
def get_bill_data(form_data, user):

    errors= {}
    
    try:
        bill_data = query_db("SELECT * FROM history_consumption_bill WHERE user_id = %s AND bill_date BETWEEN %s AND %s", user,form_data.get("date_1"),form_data.get("date_2"))

    except Exception as e:
        errors["database_error"] = f"An error occurred: {e}"
    
    if not errors:
        return bill_data
    else:
        return None