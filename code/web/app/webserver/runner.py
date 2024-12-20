import asyncio
from flask import Flask
from . import create_app
from ..config import Config

async def run_flask_server(app,db):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, app.run)