import os

from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

load_dotenv()
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

pool = AsyncConnectionPool(
    conninfo=DATABASE_URL,
    open=False,  # start pool manually
    max_size=10,  # number of connections
)


async def get_connection():
    """
    Acquires a database connection and cursor from the global pool.

    Configures the row factory to return dictionaries. Automatically handles
    cleanup and returns the connection to the pool when the context exits.

    Yields:
        tuple: A (connection, cursor) pair.
    """

    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.cursor() as cur:
            yield conn, cur
