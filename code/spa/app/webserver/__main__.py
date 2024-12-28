import asyncio
from ..config import Config
import uvicorn
from . import app

def main():
    return
    print("START WEBSERVER")    
    uvicorn.run("app.webserver:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()