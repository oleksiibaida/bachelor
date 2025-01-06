import os
import logging

class Config:
    SQLALCHEMY_DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite+aiosqlite:///app/db/database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_SECRET_KEY = 'mysercret' #os.environ.get('SECRET_KEY') or os.urandom(24)
    # MQTT_BROKER_ADDRESS = '192.144.1.10'
    MQTT_BROKER_ADDRESS = '169.254.182.194'
    MQTT_PORT = 1883
    MQTT_SUBSCRIBE_TOPICS_LIST = ["data/#", "status/#", "test/#"]

    JWT_SECRET_KEY = 'eb71e1c71a5cc5b9745a363106061ce45c2cebd45e7b0bef4d7b0488ebe8b0c03f1fc2c149985a4946f366bf667495ca2007d03796a852f23203ff21ecd67d48d7198429ae8a6ce1773b065100de9ae3a6cd9e3f398b081eb5fec84e99a593d243cb263e7918ff6cd69755a45999d950ab352362a8873e10d178bc5a14257dc41059f6689ebc545563528b79d5698b035e397ebfefa3659c8a8b7598869adcbc0f8e37bda78442d4c61ab2d2ca51faf840355189ddc846bfd9514d9d574530b83aca954ff422a6165ae75b7bfe76bdb25223d3949a1a83de0b6c45a075c30a4bde9555a193f830d0d1c3e675803f66c01f34b9ea58d53480052a70205cdbe29d'
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRE_TIME = 3600 # in seconds

    def logger_init(name=__name__, debug = True):
        logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(filename)s -  %(funcName)s - %(levelname)s - %(message)s')        
        logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
        logger = logging.getLogger(__name__)
        if debug:
            logger.setLevel(logging.DEBUG)
        return logger  