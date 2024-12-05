import sqlite3
from flask import g
# from config.logger_config import logger_init
import threading
import logging
# _logger = logger_init()
_logger = logging.getLogger(__name__)
DATABASE = 'database.db'

class Database:
    def __init__(self):
        self._thread_local = threading.local()
        
    def __getattr__(self, name):
        """
        This method intercepts attribute access and ensures the connection is established before use.
        """
        self.connect()  # Ensure connection is established
        return getattr(self._thread_local, name)

    def connect(self):
        if not hasattr(self._thread_local, 'connection'):
            self._thread_local.connection = sqlite3.connect(DATABASE)
            self._thread_local.connection.row_factory = sqlite3.Row
            self._thread_local.cursor = self._thread_local.connection.cursor()
            _logger.debug(msg=f"CONNECTED THREAD:{threading.get_ident()}")

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users(
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT UNIQUE NOT NULL,
                email       TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                firstname   VARCHAR (50),
                lastname    VARCHAR (50),
                birthday    DATE
            )
            ''')
        self._thread_local.connection.commit()

        self._thread_local.cursor.execute('''
            CREATE TABLE IF NOT EXISTS userdevice(
                user_id         UNSIGNED INT NOT NULL,
                device_id       VARCHAR (10) NOT NULL,
                PRIMARY KEY (user_id, device_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        self._thread_local.connection.commit()
        _logger.info(msg="TABLES CREATED")

    def add_user(self, user_data):
        global _logger
        try:
            if not isinstance(user_data, dict) or user_data['username'] is None or user_data['email'] is None or user_data['password'] is None or self.username_exists(user_data['username']):
                return 0
            sql = f'''
                INSERT OR REPLACE INTO users (username, email, password) 
                VALUES ('{user_data.get('username')}', '{user_data.get('email')}', '{user_data.get('password')}')
            '''
            _logger.debug(msg=f'SQL {sql}')
            self.cursor.execute(sql)
            self.connection.commit()
            _logger.info(msg=f"User added: {user_data.get('username')}")
            return 1
        except Exception as e:
            _logger.error(msg=e)
        finally:
            self.close()

    def add_userdevice(self, user_id, device_id):
        global _logger

        try:
            sql = '''
                INSERT OR REPLACE INTO userdevice (user_id, device_id)
                VALUES (?, ?)
            '''
            _logger.debug(msg=f'SQL {sql}')
            self.cursor.execute(sql, (user_id, device_id))
            self.connection.commit()
            _logger.info(msg=f"USERDEVICE ADDED {user_id}: {device_id}")
            return 1
        except Exception as e:
            _logger.error(msg=e)
            return 0
        finally:
            self.close()
        
    
    def username_exists(self, username):
        """Checks if a username is in database."""
        try:
            sql = "SELECT * FROM users WHERE username = ?"
            _logger.debug(msg=f"SQL {sql}")
            self.cursor.execute(sql, (username,))
            user = self.cursor.fetchone()
            return user is not None
        except Exception as e:
            _logger.error(msg=e)
            return 0
        finally:
            self.close()


    def email_exists(self, email):
        """Check if email is in database"""
        try:
            sql = "SELECT * FROM users WHERE email = ?"
            _logger.debug(msg=f"SQL {sql}")
            self.cursor.execute(sql, (email,))
            email = self.cursor.fetchone()
            return email is not None
        except Exception as e:
            _logger.error(msg=e)
            return 0
        finally:
            self.close()

    def get_user_data(self, username = None, email = None):
        try:
            sql = "SELECT * FROM users WHERE "
            if username is not None:
                sql += "username = ?"
                self.cursor.execute(sql, (username,))
            elif email is not None:
                sql+= "email = ?"
                self.cursor.execute(sql, (email,))
            else:
                return 0
            return dict(self.cursor.fetchone())
        except Exception as e:
            _logger.error(msg=e)
            return 0
        finally:
            self.close()
    
    def get_user_data_all(self):
        sql = "SELECT * FROM user"
        self.cursor.execute(sql)
        res = self.cursor.fetchall()
        return [dict(row) for row in res]
    
    def user_password_check(self, password, username=None, email=None):
        try:
            if username is not None:
                sql = "SELECT password FROM users WHERE username = ?"
                self.cursor.execute(sql,(username,))
            elif email is not None:
                sql = "SELECT password FROM users WHERE email = ?"
                self.cursor.execute(sql,(email,))
            else:
                return 0
            pas = self.cursor.fetchone()
            return pas == password
        except Exception as e:
            _logger.error(msg=e)
            return 0
        finally:
            self.close()

    def show_tables(self):
        self.cursor.execute("""SELECT name 
            FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name;
            """)
        return [dict(row) for row in self.cursor.fetchall()]

    
    def close(self):
        if hasattr(self._thread_local, 'connection'):
            self._thread_local.connection.close()
            del self._thread_local.connection
            _logger.debug("CLOSED THREAD %s", threading.get_ident())

    def delete_all_tables(self):
        self.cursor.execute("DROP TABLE users")
        self.cursor.execute("DROP TABLE userdevice")

db = Database()
print(db.show_tables())
print(db.get_user_data_all())
        