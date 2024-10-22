import asyncio
import os
from contextlib import asynccontextmanager

import discord
import dotenv
from discord.ext import commands
from fastapi import FastAPI

from cogs.database import Database

dotenv.load_dotenv()
discord.utils.setup_logging()

bot = commands.Bot([], intents=discord.Intents.default())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.initialize()
    asyncio.create_task(bot.start(os.getenv("discord")))
    yield
    async with asyncio.timeout(60):
        await Database.pool.close()


app = FastAPI(lifespan=lifespan)
