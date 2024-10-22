import os

import discord
import dotenv
from discord import app_commands
from discord.ext import commands

from .database import Database

dotenv.load_dotenv()


class ToolsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="url", description="※上級者向け 認証用URLを取得します")
    async def urlCommand(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="⚠️エラーが発生しました", description="あなたはこのコマンドを実行する権限を持ってません！", colour=discord.Colour.red())
            await interaction.followup.send(ephemeral=True, embed=embed)
        await interaction.response.defer(ephemeral=True)
        row = await Database.pool.fetchrow("SELECT * FROM guilds WHERE id = $1", interaction.guild.id)
        if not row:
            embed = discord.Embed(title=f"⚠️エラーが発生しました", description=f"まだ認証パネルを設置していないようです！\n`/authpanel` コマンドを使用して、認証パネルを設置してください。", colour=discord.Colour.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
        embed = discord.Embed(title=f"{interaction.guild.name} 用のURL", description=f"{os.getenv("oauth2_url")}&state={interaction.guild.id}\n**⚠️ボットをサーバーに入れている間のみ動作します**", colour=discord.Colour.og_blurple())
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ToolsCog(bot))
