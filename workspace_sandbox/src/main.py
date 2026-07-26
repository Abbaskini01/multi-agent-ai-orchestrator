# -*- coding: utf-8 -*-
import sqlite3

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('expenses.db')
        print(sqlite3.version)
    except sqlite3.Error as e:
        print(e)

    return conn


def create_table(conn, table_name):
    sql = f'''CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL
    );'''
    try:
        c = conn.cursor()
        c.execute(sql)
    except sqlite3.Error as e:
        print(e)


def insert_data(conn, data):
    sql = ''' INSERT INTO expenses (date, category, description, amount)
              VALUES(?,?,?,?) '''
    try:
        c = conn.cursor()
        c.execute(sql, data)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(e)
        return False


def list_all_expenses(conn):
    sql = ''' SELECT * FROM expenses '''
    try:
        c = conn.cursor()
        c.execute(sql)
        return c.fetchall()
    except sqlite3.Error as e:
        print(e)


if __name__ == '__main__':
    print("Expense Tracker CLI Application")
    connection = create_connection()
    if connection is not None:
        with connection:
            print("Connected to SQLite Database")
            create_table(connection, 'expenses')
            while True:
                print("Available Commands:")
                print("1. Add expense")
                print("2. List all expenses")
                print("3. Quit")
                choice = input("Enter your choice: ")
                if choice == '1':
                    date = input("Enter expense date (YYYY-MM-DD): ")
                    category = input("Enter expense category: ")
                    description = input("Enter expense description: ")
                    amount = float(input("Enter expense amount: $ "))
                    data = (date, category, description, amount)
                    if insert_data(connection, data):
                        print("Expense successfully added.")
                    else:
                        print("Failed to add expense.")
                elif choice == '2':
                    results = list_all_expenses(connection)
                    if results:
                        print("Expenses:")
                        for row in results:
                            print(f"ID: {row[0]}\nDate: {row[1]}\nCategory: {row[2]}\nDescription: {row[3]}\nAmount: {row[4]}")
                    else:
                        print("No expenses recorded.")
                elif choice == '3':
                    break
                else:
                    print("Invalid choice. Please choose a valid option.")
    else:
        print("Error! Cannot create the database connection.")