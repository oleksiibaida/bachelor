import sqlite3
from flask import g
from config.logger_config import logger_init
import threading

_logger = logger_init()

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
                password    TEXT NOT NULL    
            
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
            if not isinstance(user_data, dict):
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

    def add_userdevice(self, user_id, device_id):
        global _logger
        sql = '''
            INSERT OR REPLACE INTO userdevice (user_id, device_id)
            VALUES (?, ?)
        '''
        _logger.debug(msg=f'SQL {sql}')
        self.cursor.execute(sql, (user_id, device_id))
        self.connection.commit()
        _logger.info(msg=f"Device added for user_id {user_id}: {device_id}")
        return 1
    
    def username_exists(self, username):
        """Checks if a username already exists in the database."""
        sql = "SELECT * FROM users WHERE username = '?'"
        _logger.debug(msg=f"SQL {sql}")
        self.cursor.execute(sql, (username))
        user = self.cursor.fetchone()
        return user is not None
    
    def close(self):
        if hasattr(self._thread_local, 'connection'):
            self._thread_local.connection.close()
            del self._thread_local.connection
            _logger.debug("CONNECTION CLOSED; THREAD %s", threading.get_ident())
        