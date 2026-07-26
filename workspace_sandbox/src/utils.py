# Utility functions
import sqlite3

# Function to get database connection
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect('expenses.db')
        return conn
    except sqlite3.error as e:
        print(e)

# Function to check if table exists
def check_table_exists(conn, table_name):
    cur = conn.cursor()
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if cur.fetchone() is not None:
        return True
    else:
        return False