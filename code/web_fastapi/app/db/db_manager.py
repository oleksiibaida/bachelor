import sqlite3

class db:
    def __init__(self):
        self.connection = sqlite3.connect('app/db/database.db')
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def get_all_users(self):
        sql = "SELECT * FROM user"
        res = self.cursor.execute(sql).fetchall()
        return [dict(row) for row in res]
    
    def get_tables(self):
        sql ="SELECT name FROM sqlite_master WHERE type='table'"
        res = self.cursor.execute(sql).fetchall()
        return [dict(row) for row in res]

db = db()
us = db.get_all_users()
print(us)