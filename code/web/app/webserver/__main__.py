import asyncio
from app.config import Config
from . import create_app
from .runner import run_flask_server

async def main():
    print("START WEBSERVER")
    app, db = create_app(Config)
    await run_flask_server(app, db)

if __name__ == "__main__":
    asyncio.run(main())