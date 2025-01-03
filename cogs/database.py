import os

import asyncpg
import dotenv

dotenv.load_dotenv()


class Database:
    pool: asyncpg.Pool = None

    @classmethod
    async def initialize(cls):
        cls.pool = await asyncpg.create_pool(os.getenv("dsn"), statement_cache_size=0)
