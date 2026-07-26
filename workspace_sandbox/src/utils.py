import sqlite3

def create_table(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE,
        category TEXT,
        amount REAL,
        description TEXT
    )''')

def insert_expense(cursor, date, category, amount, description):
    cursor.execute('INSERT INTO expenses (date, category, amount, description) VALUES (?, ?, ?, ?)', (date, category, amount, description))

def view_expenses(cursor):
    cursor.execute('SELECT * FROM expenses')
    rows = cursor.fetchall()
    for row in rows:
        print(f'Date: {row[1]}, Category: {row[2]}, Amount: {row[3]}, Description: {row[4]}')