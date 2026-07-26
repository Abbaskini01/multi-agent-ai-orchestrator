# Python 3.x
# -*- coding: utf-8 -*-

# Utility functions for Expense Tracker CLI Application

import sqlite3

# Create a table in the SQLite database
def create_table(conn, table_name, columns):
    sql = f'CREATE TABLE IF NOT EXISTS {table_name} ({columns});'
    try:
        c = conn.cursor()
        c.execute(sql)
    except sqlite3.Error as e:
        print(e)


# Function to handle user input for date
def get_date_from_user():
    while True:
        date = input('Enter expense date (YYYY-MM-DD): ')
        try:
            # Basic date format validation
            year, month, day = map(int, date.split('-'))
            if not (1 <= year <= 9999 and 1 <= month <= 12 and 1 <= day <= 31):
                print('Invalid date. Please use YYYY-MM-DD format.')
            else:
                return date
        except ValueError:
            print('Invalid date format. Please use YYYY-MM-DD.')


# Function to handle user input for category
def get_category_from_user():
    category = input('Enter expense category: ')
    if category:
        return category
    else:
        print('Category cannot be empty.')
        return get_category_from_user()


# Function to handle user input for description
def get_description_from_user():
    description = input('Enter expense description: ')
    if description:
        return description
    else:
        print('Description cannot be empty.')
        return get_description_from_user()


# Function to handle user input for amount
def get_amount_from_user():
    while True:
        try:
            amount = float(input('Enter expense amount: $ '))
            if amount < 0:
                print('Expenses cannot be negative.')
            else:
                return amount
        except ValueError:
            print('Invalid amount. Please enter a number.')