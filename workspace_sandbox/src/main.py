# Importing Libraries
import sqlite3
from sqlite3 import Error
import os
import sys

# Create a new database if the database doesn't already exist
def create_database():
    try:
        conn = sqlite3.connect('expenses.db')
        print(sqlite3.version)
        return conn
    except Error as e:
        print(e)

# Create table
def create_table(conn):
    sql = '''CREATE TABLE IF NOT EXISTS expenses (
                id integer PRIMARY KEY,
                date text NOT NULL,
                category text NOT NULL,
                amount real NOT NULL
            );'''
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)

# Insert a new row into the expenses table
def insert_expense(conn, expense):
    sql = '''INSERT INTO expenses(date, category, amount)
             VALUES(?,?,?)'''
    try:
        c = conn.cursor()
        c.execute(sql, expense)
        conn.commit()
        return c.lastrowid
    except Error as e:
        print(e)

# Select all rows from the expenses table
def select_all(conn):
    sql = '''SELECT * FROM expenses'''
    try:
        c = conn.cursor()
        c.execute(sql)
        rows = c.fetchall()
        for row in rows:
            print(row)
    except Error as e:
        print(e)

# Main Function with example usage
if __name__ == '__main__':
    database = create_database()
    create_table(database)
    with database:
        print("Selecting all expenses")
        select_all(database)
        new_expense = ('2024-01-01', 'Rent', 1000.0)
        insert_expense(database, new_expense)
        print("Selecting all expenses after insert")
        select_all(database)
