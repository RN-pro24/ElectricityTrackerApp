import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash

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
        if query_db("SELECT * FROM users WHERE user_name = %s", request_user):
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
        "SELECT * FROM users WHERE user_name = %s", form_data.get("username")
    )

    # Ensure username exists and password is correct
    if len(user_data) != 1 or not check_password_hash(
        user_data[0]["password"], form_data.get("password")
    ):
        errors["access"] = "invalid username and/or password"
        return errors, None
    
    else:
        return errors, user_data
