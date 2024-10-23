import asyncio
import os
import traceback
from contextlib import asynccontextmanager

import discord
import dotenv
from discord.ext import commands
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from cogs.database import Database

dotenv.load_dotenv()
discord.utils.setup_logging()

bot = commands.Bot("nya!", intents=discord.Intents.default())


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.tools")
    await bot.load_extension("cogs.panel")
    await bot.load_extension("cogs.authpage")
    app.add_api_route(
        "/callback",
        bot.cogs.get("AuthPageCog").discordCallback,
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    await bot.load_extension("cogs.call")


@bot.command("load")
async def loadCommand(ctx: commands.Context, *, module: str):
    if ctx.author.id == 1048448686914551879:
        try:
            await bot.load_extension(module)
            await ctx.reply("ok")
        except Exception as e:
            traceback.print_exc()
            await ctx.reply(e)
    else:
        return


@bot.command("reload")
async def reloadCommand(ctx: commands.Context, *, module: str):
    if ctx.author.id == 1048448686914551879:
        try:
            await bot.reload_extension(module)
            await ctx.reply("ok")
        except Exception as e:
            traceback.print_exc()
            await ctx.reply(e)
    else:
        return


@bot.command("sync")
async def syncCommand(ctx: commands.Context):
    if ctx.author.id == 1048448686914551879:
        await bot.tree.sync()
        await ctx.reply("ok")
    else:
        return


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.initialize()
    asyncio.create_task(bot.start(os.getenv("discord")))
    yield
    async with asyncio.timeout(60):
        await Database.pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/", response_class=RedirectResponse)
async def index():
    return RedirectResponse(
        "https://discord.com/oauth2/authorize?client_id=1298239893608337440"
    )
