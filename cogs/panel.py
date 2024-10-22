import os

import discord
import dotenv
from discord import app_commands
from discord.ext import commands

from .database import Database

dotenv.load_dotenv()


class PanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="authpanel", description="認証パネルを設置します")
    async def authPanelCommand(
        self,
        interaction: discord.Interaction,
        name: str = "認証",
        description: str = "このサーバーを利用するには、認証が必要です！\n今すぐ「認証」ボタンを押して、認証を開始しましょう！",
        botton_text: str = "認証",
    ):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description="あなたはこのコマンドを実行する権限を持ってません！",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(ephemeral=True, embed=embed)
        await interaction.response.defer(ephemeral=True)
        # 記述していません


async def setup(bot: commands.Bot):
    await bot.add_cog(PanelCog(bot))
