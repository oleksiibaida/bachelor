import os
import logging

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite+aiosqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_SECRET_KEY = 'mysercret' #os.environ.get('SECRET_KEY') or os.urandom(24)
    MQTT_BROKER_ADDRESS = '192.144.1.10'
    MQTT_PORT = 1883
    MQTT_SUBSCRIBE_TOPICS_LIST = ["data/#"]

    def logger_init(name=__name__, debug = True):
        logging.basicConfig(level=logging.DEBUG,  # Set the minimum logging level to DEBUG
                        format='%(asctime)s - %(filename)s -  %(funcName)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        if debug:
            logger.setLevel(logging.DEBUG)
        return logger  