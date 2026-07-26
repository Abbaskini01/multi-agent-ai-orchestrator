import sqlite3
from sqlite3 import Error


class ExpenseTracker:
    def __init__(self, db_file):
        self.conn = None
        try:
            self.conn = sqlite3.connect(db_file)
            print(sqlite3.version)
        except Error as e:
            print(e)

    def create_table(self):
        sql_create_expenses_table = '''CREATE TABLE IF NOT EXISTS expenses (
                                        id integer PRIMARY KEY,
                                        date text NOT NULL,
                                        category text NOT NULL,
                                        amount real NOT NULL
                                    );'''
        try:
            c = self.conn.cursor()
            c.execute(sql_create_expenses_table)
        except Error as e:
            print(e)

    def insert_expense(self, expense):
        sql = ''' INSERT INTO expenses(date,category,amount)
                  VALUES(?,?,?) '''
        try:
            c = self.conn.cursor()
            c.execute(sql, expense)
            self.conn.commit()
            return c.lastrowid
        except Error as e:
            print(e)

    def select_all_expenses(self):
        sql = ''' SELECT * FROM expenses'''
        try:
            c = self.conn.cursor()
            c.execute(sql)
            rows = c.fetchall()
            return rows
        except Error as e:
            print(e)

    def close_connection(self):
        if self.conn:
            self.conn.close()


if __name__ == '__main__':
    expense_tracker = ExpenseTracker('expenses.db')
    expense_tracker.create_table()
    while True:
        print("1. Add Expense")
        print("2. View All Expenses")
        print("3. Exit")
        choice = input("Choose an option: ")
        if choice == '1':
            date = input("Enter date (YYYY-MM-DD): ")
            category = input("Enter category: ")
            amount = float(input("Enter amount: "))
            expense = (date, category, amount)
            expense_id = expense_tracker.insert_expense(expense)
            print(f"Expense added with id {expense_id}")
        elif choice == '2':
            rows = expense_tracker.select_all_expenses()
            for row in rows:
                print(row)
        elif choice == '3':
            break
        else:
            print("Invalid option. Please choose again.")
    expense_tracker.close_connection()