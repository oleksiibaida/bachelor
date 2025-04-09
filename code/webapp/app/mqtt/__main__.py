import asyncio
from .client import MQTTClient
from app.config import Config
logger = Config.logger_init()
async def main():
    return
    # await MQTTClient.subscribe(Config.MQTT_SUBSCRIBE_TOPICS_LIST)
    


# if __name__ == "__main__":
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#     asyncio.run(main())