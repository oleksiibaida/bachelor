import os

class FlaskConfig():
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), '../database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'mysercret' #os.environ.get('SECRET_KEY') or os.urandom(24)
    