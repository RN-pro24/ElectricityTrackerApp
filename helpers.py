import mysql.connector

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
