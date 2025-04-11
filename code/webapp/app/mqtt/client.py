import aiomqtt
import os
import json
from app.config import Config

logger = Config.logger_init()

class MQTTClient():
    @classmethod
    async def start_client(cls, topics: list):
        """
        Receives MQTT-messages
        Must be called with asyncio.create_task()
        :param topics: List of topics client subscribes to
        """
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
        """
        Work with received message
        :param message: payload of message
        """
        try:
            # get device_id from topic
            main_topic, device_id = str(message.topic).split('/')
            msg = message.payload.decode()
            
            # Recieved from alarm
            if main_topic == "alarm":
                data = {"alarm":msg}
            else: 
                data = json.loads(msg)      

            # Update data on handshake message
            if main_topic == 'handshake':
                print(data)
                from app.db import queries, get_direct_session, close_session
                session =  await get_direct_session()
                await queries.update_device_handshake_data(session, device_id, data)
                await close_session(session)

            # Work with scenario
            scenarios = cls.saved_scenarios.get(device_id)
            if scenarios is not None: 
                for sc in scenarios:
                    # Check condition
                    if eval(f"{data[sc.data_field]} {sc.condition.value} {sc.value}"):  
                        # print(f"{data[sc.data_field]} {sc.condition.value} {sc.value}")
                        if not sc.active: # scenario is not active
                            sc.active = True
                            await cls.send_command_to_device(sc.target_dev, sc.command)
                    elif sc.active: sc.active = False

            from app.webserver.services import WebsocketHandler
            await WebsocketHandler.send_data(device_id, data)          
        except Exception as e:
            logger.error(e)

    @classmethod
    async def publish(cls, topic, message):
        """
        Sends message in given topic
        """
        async with aiomqtt.Client(hostname=Config.MQTT_BROKER_ADDRESS, port=Config.MQTT_PORT) as client:
            print(f'PUBLISH {topic}:{message}')
            client.publish(topic=topic, payload=message)

    async def send_command_to_device(device_id: str, command: str):
        """
        Sends command to device. Topic command/device_id
        
        """
        async with aiomqtt.Client(hostname=Config.MQTT_BROKER_ADDRESS, port=Config.MQTT_PORT) as client:
            topic = "command/" + device_id
            print(f"SENT COMMAND TO {device_id}: {topic}:{command}")
            await client.publish(topic, command)

    saved_scenarios = {} # {"source_dev": [scenario1, scneario2]}

    @classmethod
    async def load_scenarios(cls):
        from app.db import queries, get_direct_session, close_session
        session = await get_direct_session()
        res = await queries.get_all_scenarios(session)
        await close_session(session)
        
        for scenario in res:
            # set all scenarios to unactive
            scenario.active = False
            if scenario.source_dev in cls.saved_scenarios:
                cls.saved_scenarios[scenario.source_dev].append(scenario)
            else: 
                cls.saved_scenarios[scenario.source_dev] = [scenario]
            print(scenario.name)
        print(cls.saved_scenarios)
        return
    

    async def send_handshake(device_id):
        async with aiomqtt.Client(hostname=Config.MQTT_BROKER_ADDRESS, port=Config.MQTT_PORT) as client:
            topic = "command/" + device_id
            await client.publish(topic, "handshake")
    