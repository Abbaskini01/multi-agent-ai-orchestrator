import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    return conn


def create_table(conn, table_name):
    sql = f''' CREATE TABLE IF NOT EXISTS {table_name} (
                        id integer PRIMARY KEY,
                        date text NOT NULL,
                        description text NOT NULL,
                        amount real NOT NULL
                    ); '''
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)


def insert_data(conn, table_name, data):
    sql = f''' INSERT INTO {table_name}(date,description,amount)
                VALUES(?,?,?) '''
    try:
        c = conn.cursor()
        c.execute(sql, data)
        conn.commit()
        return c.lastrowid
    except Error as e:
        print(e)


def get_all_data(conn, table_name):
    sql = f''' SELECT * FROM {table_name}'''
    try:
        c = conn.cursor()
        c.execute(sql)
        rows = c.fetchall()
        return rows
    except Error as e:
        print(e)


def update_data(conn, table_name, id, data):
    sql = f''' UPDATE {table_name}
                SET date = ?, description = ?, amount = ? 
                WHERE id = ?'''
    try:
        c = conn.cursor()
        c.execute(sql, data)
        conn.commit()
    except Error as e:
        print(e)


def delete_data(conn, table_name, id):
    sql = f''' DELETE FROM {table_name} WHERE id=?'''
    try:
        c = conn.cursor()
        c.execute(sql, (id,))
        conn.commit()
    except Error as e:
        print(e)


def main():
    database = 'expenses.db'
    table_name = 'expenses'
    conn = create_connection(database)
    if conn is not None:
        create_table(conn, table_name)
    else:
        print('Error! Cannot create the database connection.')

    while True:
        print('\n1. Insert Data')
        print('2. Get All Data')
        print('3. Update Data')
        print('4. Delete Data')
        print('5. Exit')
        choice = input('Enter your choice: ')
        if choice == '1':
            date = input('Enter date: ')
            description = input('Enter description: ')
            amount = float(input('Enter amount: '))
            insert_data(conn, table_name, (date, description, amount))
        elif choice == '2':
            rows = get_all_data(conn, table_name)
            for row in rows:
                print(row)
        elif choice == '3':
            id = int(input('Enter id: '))
            date = input('Enter date: ')
            description = input('Enter description: ')
            amount = float(input('Enter amount: '))
            update_data(conn, table_name, id, (date, description, amount, id))
        elif choice == '4':
            id = int(input('Enter id: '))
            delete_data(conn, table_name, id)
        elif choice == '5':
            break
        else:
            print('Invalid choice. Please try again.')


if __name__ == '__main__':
    main()