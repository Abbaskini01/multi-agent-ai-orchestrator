import sqlite3
from datetime import datetime


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)


def create_table(conn, table_name):
    sql = f'''CREATE TABLE IF NOT EXISTS {table_name} (
                id integer PRIMARY KEY,
                date text NOT NULL,
                category text NOT NULL,
                amount real NOT NULL
            ); '''
    try:
        c = conn.cursor()
        c.execute(sql)
    except sqlite3.Error as e:
        print(e)


def add_expense(conn, expense):
    sql = '''INSERT INTO expenses(date, category, amount)
              VALUES(?,?,?) '''
    try:
        c = conn.cursor()
        c.execute(sql, expense)
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        print(e)


def get_all_expenses(conn, table_name):
    sql = f'''SELECT * FROM {table_name}'''
    try:
        c = conn.cursor()
        c.execute(sql)
        rows = c.fetchall()
        return rows
    except sqlite3.Error as e:
        print(e)


def main():
    database = 'expenses.db'
    table_name = 'expenses'
    conn = create_connection(database)
    if conn is not None:
        create_table(conn, table_name)
        while True:
            print('1. Add Expense\n2. View Expenses\n3. Quit')
            choice = input("Choose an option: ")
            if choice == '1':
                date = datetime.now().strftime('%Y-%m-%d')
                category = input('Enter category: ')
                amount = float(input('Enter amount: '))
                expense = (date, category, amount)
                add_expense(conn, expense)
                print('Expense added successfully.')
            elif choice == '2':
                rows = get_all_expenses(conn, table_name)
                for row in rows:
                    print(row)
            elif choice == '3':
                break
            else:
                print('Invalid choice')
        conn.close()
    else:
        print("Error! Cannot create the database connection.")


if __name__ == '__main__':
    main()