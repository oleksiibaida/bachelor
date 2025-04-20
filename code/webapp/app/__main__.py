"""
    Author: O. Baida

    Startet die Anwendung
"""
import asyncio
import uvicorn
from app import db
async def main():
    await db.create_tables() 
    
if __name__=='__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    uvicorn.run("app.webserver:app", host="0.0.0.0", port=8000, reload=True)