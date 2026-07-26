import sqlite3

conn = sqlite3.connect('expenses.db')
cursor = conn.cursor()

cursor.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, amount REAL)')
conn.commit()

def get_expenses(cursor):
    cursor.execute('SELECT * FROM expenses')
    return cursor.fetchall()

def add_expense(cursor, name, amount):
    cursor.execute('INSERT INTO expenses (name, amount) VALUES (?, ?)', (name, amount))

def delete_expense(cursor, id):
    cursor.execute('DELETE FROM expenses WHERE id = ?', (id,))