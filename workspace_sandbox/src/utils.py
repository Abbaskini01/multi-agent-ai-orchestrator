import sqlite3

def create_table(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date text, category text, amount real)''')

def insert_data(conn):
    c = conn.cursor()
    date = input("Enter date (YYYY-MM-DD): ")
    category = input("Enter category: ")
    amount = float(input("Enter amount: "))
    c.execute("INSERT INTO expenses (date, category, amount) VALUES (?, ?, ?)", (date, category, amount))

def view_data(conn):
    c = conn.cursor()
    c.execute("SELECT * FROM expenses")
    rows = c.fetchall()
    for row in rows:
        print(row)