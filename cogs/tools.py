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

    @app_commands.command(name="url", description="※上級者向け 認証用URLを表示")
    @app_commands.allowed_contexts(guilds=True, dms=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def urlCommand(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description="あなたはこのコマンドを実行する権限を持ってません！",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(ephemeral=True, embed=embed)
            return
        await interaction.response.defer(ephemeral=True)
        row = await Database.pool.fetchrow(
            "SELECT * FROM guilds WHERE id = $1", interaction.guild.id
        )
        if not row:
            embed = discord.Embed(
                title=f"⚠️エラーが発生しました",
                description=f"まだ認証パネルを設置していないようです！\n`/authpanel` コマンドを使用して、認証パネルを設置してください。",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        oauth2Url = os.getenv("oauth2_url")
        embed = discord.Embed(
            title=f"{interaction.guild.name} 用のURL",
            description=f"{oauth2Url}&state={interaction.guild.id}\n**⚠️ボットをサーバーに入れている間のみ動作します**",
            colour=discord.Colour.og_blurple(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="authcount", description="このサーバーで認証した人の数を表示"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def authCountCommand(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description="あなたはこのコマンドを実行する権限を持ってません！",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(ephemeral=True, embed=embed)
            return
        await interaction.response.defer(ephemeral=True)
        row = await Database.pool.fetchrow(
            "SELECT * FROM guilds WHERE id = $1", interaction.guild.id
        )
        if not row:
            embed = discord.Embed(
                title=f"⚠️エラーが発生しました",
                description=f"まだ認証パネルを設置していないようです！\n`/authpanel` コマンドを使用して、認証パネルを設置してください。",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(
            title="認証済みメンバーの数",
            description=f'今までに認証したメンバー: {len(row["authorized_members"])}人\n最後の`/call`から認証したメンバー: {row["authorized_count"]}人',
            colour=discord.Colour.og_blurple(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="users", description="登録されているユーザーの数を表示")
    @app_commands.allowed_contexts(guilds=True, dms=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def usersCommand(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        userCount = await Database.pool.fetchval("SELECT COUNT(*) FROM users")
        embed = discord.Embed(
            title="登録されているユーザー", description=f"累計: {userCount}人"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="serverid", description="サーバーIDを確認")
    @app_commands.allowed_contexts(guilds=True, dms=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def serverIdCommand(self, interaction: discord.Interaction):
        await interaction.response.send_message(str(interaction.guild.id), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ToolsCog(bot))
