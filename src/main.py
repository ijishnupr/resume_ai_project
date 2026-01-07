from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.router import router
from src.shared.db import pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open()  # initialize PostgreSQL async pool
    yield
    await pool.close()  # close pool safely


app = FastAPI(lifespan=lifespan)

app.include_router(router, prefix="/api")


app.add_middleware(
    CORSMiddleware,  # ty:ignore[invalid-argument-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status/")
def root():
    return {"message": "Server status is healthy"}
