from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.router import router
from shared.db import pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open()  # initialize PostgreSQL async pool
    yield
    await pool.close()  # close pool safely


app = FastAPI(lifespan=lifespan)

app.include_router(router, prefix="/api")


@app.get("/api/status/")
def root():
    return {"message": "Server status is healthy"}
