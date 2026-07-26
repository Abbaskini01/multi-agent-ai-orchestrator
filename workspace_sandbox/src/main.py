import sqlite3
import argparse

DATABASE = 'expenses.db'

CREATE_TABLE_QUERY = '''CREATE TABLE IF NOT EXISTS expenses(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT NOT NULL,
                            category TEXT NOT NULL,
                            amount REAL NOT NULL
                            );'''

INSERT_QUERY = '''INSERT INTO expenses(date, category, amount) VALUES(?, ?, ?)'''

SELECT_QUERY = '''SELECT * FROM expenses'''

DELETE_QUERY = '''DELETE FROM expenses WHERE id = ?'''

UPDATE_QUERY = '''UPDATE expenses SET date = ?, category = ?, amount = ? WHERE id = ?'''


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except sqlite3.Error as e:
        print(e)
    return conn


def create_expense(conn, expense):
    sql = INSERT_QUERY
    cur = conn.cursor()
    cur.execute(sql, expense)
    conn.commit()
    return cur.lastrowid


def select_all_expenses(conn):
    cur = conn.cursor()
    cur.execute(SELECT_QUERY)
    rows = cur.fetchall()
    return rows


def delete_expense(conn, id):
    sql = DELETE_QUERY
    cur = conn.cursor()
    cur.execute(sql, (id,))
    conn.commit()


def update_expense(conn, expense):
    sql = UPDATE_QUERY
    cur = conn.cursor()
    cur.execute(sql, expense)
    conn.commit()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Expense Tracker')
    sub_parsers = parser.add_subparsers(dest='command')

    add_parser = sub_parsers.add_parser('add')
    add_parser.add_argument('-d', '--date', required=True)
    add_parser.add_argument('-c', '--category', required=True)
    add_parser.add_argument('-a', '--amount', required=True, type=float)

    sub_parsers.add_parser('list')

    delete_parser = sub_parsers.add_parser('delete')
    delete_parser.add_argument('-i', '--id', required=True, type=int)

    update_parser = sub_parsers.add_parser('update')
    update_parser.add_argument('-i', '--id', required=True, type=int)
    update_parser.add_argument('-d', '--date', required=True)
    update_parser.add_argument('-c', '--category', required=True)
    update_parser.add_argument('-a', '--amount', required=True, type=float)

    args = parser.parse_args(argv)

    conn = create_connection(DATABASE)
    if conn is not None:
        if args.command == 'add':
            expense = (args.date, args.category, args.amount)
            expense_id = create_expense(conn, expense)
            print(f'Expense added with id {expense_id}')
        elif args.command == 'list':
            expenses = select_all_expenses(conn)
            for row in expenses:
                print(row)
        elif args.command == 'delete':
            delete_expense(conn, args.id)
            print(f'Expense with id {args.id} has been deleted')
        elif args.command == 'update':
            expense = (args.date, args.category, args.amount, args.id)
            update_expense(conn, expense)
            print(f'Expense with id {args.id} has been updated')
        else:
            print('Invalid command')
    else:
        print('Error! cannot create the database connection.')


if __name__ == '__main__':
    main()