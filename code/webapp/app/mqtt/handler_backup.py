import asyncio
import asyncio_mqtt as aiomqtt
from app.config import Config
from .client import MQTTClient
from app.webserver.services import WebsocketHandler
import json
_logger = Config.logger_init(debug=True);

class MQTTHandler():
    
    async def listen_topics():
        async for message in MQTTClient.subscribe(Config.MQTT_SUBSCRIBE_TOPICS_LIST):
            _logger.info(f"PROCESSING {message}")
            # get device_id from topic
            main_topic, device_id = str(message.topic).split('/')    
            msg=message.payload.decode()
            await WebsocketHandler.send_data(device_id, json.loads(msg))
