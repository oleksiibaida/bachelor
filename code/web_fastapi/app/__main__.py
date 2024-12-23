import sys, os
import asyncio
import threading

import uvicorn
from app.config import Config
from app import db
# from app.webserver import init_fastapi
from app.mqtt.client import MQTTClient
logger = Config.logger_init()
async def main():
    logger.info("START MAIN")
    config = Config()
    await db.create_tables()
    # init_fastapi
    uvicorn.run("app.webserver:app", host="0.0.0.0", port=8000, reload=True)
    


    
if __name__=='__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())