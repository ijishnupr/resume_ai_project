from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.router import router
from src.shared.db import pool
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open()  # initialize PostgreSQL async pool
    yield
    await pool.close()  # close pool safely


app = FastAPI(lifespan=lifespan)

app.include_router(router, prefix="/api")
origins = [
    "http://localhost:3000",  
    "http://127.0.0.1:3000",
    "http://localhost:5173",  
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status/")
def root():
    return {"message": "Server status is healthy"}
