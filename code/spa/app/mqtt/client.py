import aiomqtt
import os
import json
from app.config import Config

logger = Config.logger_init()

class MQTTClient():
    @classmethod
    async def start_client(cls, topics: list):
        """Receives MQTT-messages """
        while True:
            try:
                async with aiomqtt.Client(hostname=Config.MQTT_BROKER_ADDRESS, port=Config.MQTT_PORT) as client:
                    for t in topics:
                        await client.subscribe(t)
                        logger.info(f'SUBSCRIBED TOPIC {t}')
                    async for message in client.messages:
                        await cls.process_message(message)
            except aiomqtt.MqttError as e:
                logger.error(e)
                

    @classmethod
    async def process_message(cls, message):
        """ Work with received message"""
        try:
            # get device_id from topic
            main_topic, device_id = str(message.topic).split('/')
            msg = message.payload.decode()
            data = json.loads(msg)      
            
            from app.webserver.services import WebsocketHandler
            await WebsocketHandler.send_data(device_id, data)

        except Exception as e:
            logger.error(e)

