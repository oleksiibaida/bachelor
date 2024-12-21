import sys, os
import asyncio
import threading


from app import create_app_instance
from app.config import Config
from app.webserver import create_app
from app.webserver.runner import run_flask_server
# from app.db import db

logger = Config.logger_init()

def start_flask():
    return

async def main():
    logger.info("START")
    config = Config()
    flask_app, db_instance = create_app(config)

    config.db = db_instance
    try:
        await asyncio.gather(
            await run_flask_server(flask_app, db_instance)
        )
    except Exception as e:
        print(e)
    
if __name__=='__main__':
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    # loop = asyncio.get_event_loop()
    # flask_thread = threading.Thread(target=start_flask, daemon=True)
    # flask_thread.start()
    # app.run(debug=True, host='127.0.0.1', port=3000)