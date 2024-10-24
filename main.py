import asyncio
import os
import traceback
from contextlib import asynccontextmanager

import discord
import dotenv
from discord.ext import commands, tasks
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from cogs.database import Database

dotenv.load_dotenv()
discord.utils.setup_logging()

bot = commands.Bot("nya!", intents=discord.Intents.default())


@tasks.loop(seconds=20)
async def precenseLoop():
    game = discord.Game(f"{len(bot.guilds)} サーバー")
    await bot.change_presence(status=discord.Status.online, activity=game)


@bot.event
async def on_ready():
    precenseLoop.start()


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


@bot.command("send")
async def sendCommand(ctx: commands.Context, channelId: int, *, message: str):
    if ctx.author.id == 1048448686914551879:
        try:
            channel = bot.get_channel(channelId)
            if not channel:
                embed = discord.Embed(
                    title="⚠️エラーが発生しました",
                    description="チャンネルが存在しません",
                    colour=discord.Colour.red(),
                )
                await ctx.reply(embed=embed)
                return
            await channel.send(
                message,
                files=[
                    await attachment.to_file() for attachment in ctx.message.attachments
                ],
            )
            embed = discord.Embed(
                title="✅送信しました！",
                colour=discord.Colour.og_blurple(),
            )
            await ctx.reply(embed=embed)
        except Exception as e:
            traceback.print_exc()
            await ctx.reply(e)
    else:
        return


@bot.command("guild")
async def guildCommand(ctx: commands.Context, *, guildId: int):
    if ctx.author.id == 1048448686914551879:
        try:
            guild = bot.get_guild(guildId)
            if not guild:
                embed = discord.Embed(
                    title="⚠️エラーが発生しました",
                    description="ギルドが存在しません",
                    colour=discord.Colour.red(),
                )
                await ctx.reply(embed=embed)
                return
            embed = discord.Embed(
                title=guild.name,
                description=f"管理者 / ADMINISTRATOR: `{guild.owner}`\nPERMISSIONS / 権限\nSEND_MESSAGES: {guild.me.guild_permissions.send_messages}\nMANAGE_ROLES: {guild.me.guild_permissions.manage_roles}",
                colour=discord.Colour.og_blurple(),
            )
            print(guild.channels)
            await ctx.reply(embed=embed)
        except Exception as e:
            traceback.print_exc()
            await ctx.reply(e)
    else:
        return


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
