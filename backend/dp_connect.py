import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="vaultdb",   
        user="postgres",       
        password="3198"
    )
