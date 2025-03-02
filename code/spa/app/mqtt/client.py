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
                # return
                

    @classmethod
    async def process_message(cls, message):
        """ Work with received message"""
        try:
            # get device_id from topic
            main_topic, device_id = str(message.topic).split('/')
            msg = message.payload.decode()
            data = json.loads(msg)      

            # Answer on handshake message
            if main_topic == 'handshake':
                print(data)
                from app.db import queries, get_direct_session, close_session
                session =  await get_direct_session()
                await queries.update_device_handshake_data(session, device_id, data)
                await close_session(session)

            # work with scenario
            for s in cls.saved_scenarios:
                if s.source_dev == device_id:
                    if eval(f"{data[s.data_field]} {s.condition.value} {s.value}"):
                        print(f"{data[s.data_field]} {s.condition.value} {s.value}")
                        await cls.send_command_to_device(s.target_dev, s.command)

            from app.webserver.services import WebsocketHandler
            await WebsocketHandler.send_data(device_id, data)          
        except Exception as e:
            logger.error(e)

    @classmethod
    async def publish(cls, device_id, topic, message):
        async with aiomqtt.Client(hostname=Config.MQTT_BROKER_ADDRESS, port=Config.MQTT_PORT) as client:
            print(f'PUBLISH {topic}:{message}')
            client.publish(topic=topic, payload=message)

    async def send_command_to_device(device_id: str, command: str):
        async with aiomqtt.Client(hostname=Config.MQTT_BROKER_ADDRESS, port=Config.MQTT_PORT) as client:
            topic = "command/" + device_id
            await client.publish(topic, command)

    saved_scenarios = []

    @classmethod
    async def load_scenarios(cls):
        from app.db import queries, get_direct_session, close_session
        session = await get_direct_session()
        res = await queries.get_all_scenarios(session)
        for r in res:
            print(r.condition.value)
        await close_session(session)
        cls.saved_scenarios = res
        for _ in cls.saved_scenarios:
            print(_)
        return
    

    async def send_handshake(device_id):
        async with aiomqtt.Client(hostname=Config.MQTT_BROKER_ADDRESS, port=Config.MQTT_PORT) as client:
            topic = "command/" + device_id
            await client.publish(topic, "handshake")
    