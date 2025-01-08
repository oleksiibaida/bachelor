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
    
    def get_houses(self, user_id):
        sql = f"SELECT * FROM house WHERE user_id={user_id}"
        res = self.cursor.execute(sql).fetchall()
        return [dict(row) for row in res]
    
    def get_all_houses(self):
        sql = f"SELECT * FROM house"
        res = self.cursor.execute(sql).fetchall()
        return [dict(row) for row in res]
    
    def del_house(self, user_id, house_name):
        sql = f"DELETE FROM house WHERE user_id={user_id} AND name='{house_name}'"
        self.cursor.execute(sql)
        self.connection.commit()
    
    def del_all_houses(self):
        sql = 'DELETE FROM house'
        self.cursor.execute(sql)
        self.connection.commit()

    def get_all_rooms(self):
        sql = 'SELECT * FROM room' 
        res = self.cursor.execute(sql)
        return [dict(row) for row in res]

    def get_all_devices(self):
        sql = 'SELECT * FROM device'
        res = self.cursor.execute(sql)
        return [dict(row) for row in res]
    
    def get_all_room_device(self):
        sql = 'SELECT * FROM room_device'
        res = self.cursor.execute(sql)
        return [dict(row) for row in res]
    
    def clear_device(self):
        sql = 'DELETE FROM device, room_device'
        self.cursor.execute(sql)
        self.connection.commit()
    
    def test(self):
    
        # sql = 'PRAGMA table_info(device)'
        sql = 'DROP TABLE room_device'
        # sql = 'SELECT * FROM room_device rd LEFT JOIN device d ON rd.device_id = d.id'
        res = self.cursor.execute(sql)
        self.connection.commit()
        res = [dict(row) for row in res]
        for _ in res:
            print(_)



db = db()
# db.test()
# db.del_all_houses()
print('====HOUSES====')
hs = db.get_all_houses()
for h in hs:
    print(h)

print("====ROOMS====")

hs = db.get_all_rooms()
for h in hs:
    print(h)

print("====DEVICES====")
dv = db.get_all_devices()
for d in dv:
    print(d)
print("====ROOM_DEVICE====")
dv = db.get_all_room_device()
for d in dv:
    print(d)