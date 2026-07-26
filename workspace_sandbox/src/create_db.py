import sqlite3

DATABASE = 'expenses.db'

CREATE_TABLE_Query = '''CREATE TABLE IF NOT EXISTS expenses(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT NOT NULL,
                            category TEXT NOT NULL,
                            amount REAL NOT NULL
                            )'''


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except sqlite3.Error as e:
        print(e)
    return conn


def create_table(conn):
    sql = CREATE_TABLE_Query
    try:
        c = conn.cursor()
        c.execute(sql)
    except sqlite3.Error as e:
        print(e)


if __name__ == '__main__':
    conn = create_connection(DATABASE)
    create_table(conn)