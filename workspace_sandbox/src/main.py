import sqlite3
from src.utils import get_expenses, add_expense, delete_expense

conn = sqlite3.connect('expenses.db')
cursor = conn.cursor()

while True:
    print("1. Get expenses\n2. Add expense\n3. Delete expense\n4. Quit")
    choice = input('> ')
    if choice == '1':
        expenses = get_expenses(cursor)
        for expense in expenses:
            print(expense)
    elif choice == '2':
        name = input('Enter expense name: ')
        amount = float(input('Enter expense amount: '))
        add_expense(cursor, name, amount)
        conn.commit()
    elif choice == '3':
        id = int(input('Enter expense id: '))
        delete_expense(cursor, id)
        conn.commit()
    elif choice == '4':
        break
    else:
        print('Invalid choice')
