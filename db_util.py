import os
import sqlite3


def init_db(force_recreate=False):
    if not os.path.exists('./data.db') or \
            (force_recreate and
             os.path.exists('./data.db') and
             input('recreate database? (y/n):') == 'y'
             and input('are you sure? (y/n):') == 'y'):
        if force_recreate:
            print('recreating database')
            os.remove('./data.db')
        conn = sqlite3.connect('./data.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE recipe(
            recipe_name TEXT primary key,
            inputs TEXT,
            outputs TEXT,
            time REAL
        )
        ''')

    else:
        conn = sqlite3.connect('./data.db')
    return conn
