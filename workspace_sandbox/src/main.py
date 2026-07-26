#!/usr/bin/env python3
import sqlite3
from src.utils import create_table, insert_expense, view_expenses

def main():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    create_table(cursor)
    while True:
        print('1. Insert expense')
        print('2. View expenses')
        print('3. Exit')
        choice = input('Enter your choice: ')
        if choice == '1':
            date = input('Enter date (YYYY-MM-DD): ')
            category = input('Enter category: ')
            amount = float(input('Enter amount: '))
            description = input('Enter description: ')
            insert_expense(cursor, date, category, amount, description)
            conn.commit()
        elif choice == '2':
            view_expenses(cursor)
        elif choice == '3':
            break
        else:
            print('Invalid choice. Please try again.')

if __name__ == '__main__':
    main()