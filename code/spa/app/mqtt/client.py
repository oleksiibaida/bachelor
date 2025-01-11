import aiomqtt
import os
from app.config import Config
logger = Config.logger_init()

class MQTTClient:
    async def subscribe(topics: list):
        try:
            async with aiomqtt.Client(hostname=Config.MQTT_BROKER_ADDRESS) as client:
                for t in topics:
                    await client.subscribe(t)
                    logger.info(f'SUBSCRIBED TO {t} PROCESS {os.getpid()}')
                async for mes in client.messages:
                    logger.info(f"RECEIVED MESSAGE: T:{mes.topic} P:{mes.payload}")
                    # if mes.topic.matches("alarm/"):
                    #     await MQTTClient.publish("publish", "ALARM")
                    yield mes
        except aiomqtt.exceptions.MqttError as e:
            logger.error(e)

    async def publish(topic: str, message):
        async with aiomqtt.Client(hostname=Config.MQTT_BROKER_ADDRESS) as client:
            await client.publish(topic=topic, payload=message)
            logger.info(f"PUB {topic}:{message}")
