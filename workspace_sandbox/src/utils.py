# Define utility functions
import sqlite3

# Function to get all categories
def get_all_categories(conn):
    sql = '''SELECT DISTINCT category FROM expenses'''
    try:
        c = conn.cursor()
        c.execute(sql)
        rows = c.fetchall()
        return [row[0] for row in rows]
    except sqlite3.Error as e:
        print(e)

# Function to get total expenses by category
def get_total_expenses_by_category(conn, category):
    sql = '''SELECT SUM(amount) FROM expenses WHERE category = ?'''
    try:
        c = conn.cursor()
        c.execute(sql, (category,))
        row = c.fetchone()
        return row[0]
    except sqlite3.Error as e:
        print(e)
