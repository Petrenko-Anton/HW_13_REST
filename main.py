from fastapi import FastAPI
import uvicorn
from src.routes import contacts, auth, users
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter



app = FastAPI()

app.include_router(contacts.router, prefix='/api')
app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')
app.include_router(users.router, prefix='/api')

origins = [
    "http://localhost:9000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    r = await redis.Redis(host='localhost', port=6379, db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)



@app.get("/")
async def index():
    return {"msg": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000)
