from fastapi import FastAPI
import uvicorn
app = FastAPI()

@app.get("/")
async def root():
    return {"HELLO":"WORLD"}

if __name__ == "__main__":
    print("Start")