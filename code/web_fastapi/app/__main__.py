import sys, os
import asyncio
import threading

import uvicorn
from app.config import Config
from app import db
from app.webserver import app
logger = Config.logger_init()
async def main():
    logger.info("START MAIN")
    config = Config()
    await db.create_tables()
    # flask_app = create_app(config)
    uvicorn.run("app.webserver:app", host="0.0.0.0", port=8000, reload=True)

    


    
if __name__=='__main__':
    # if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    #     from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    #     set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    # loop = asyncio.get_event_loop()
    # flask_thread = threading.Thread(target=start_flask, daemon=True)
    # flask_thread.start()
    # app.run(debug=True, host='127.0.0.1', port=3000)