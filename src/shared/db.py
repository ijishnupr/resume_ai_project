import os
import psycopg
from psycopg_pool import AsyncConnectionPool
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

pool = AsyncConnectionPool(
    conninfo=DATABASE_URL,
    open=False,  # start pool manually
    max_size=10,  # number of connections
)


async def get_connection():
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.cursor() as cur:
            yield conn, cur
