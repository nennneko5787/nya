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

    @app_commands.command(
        name="authpanel",
        description="認証パネルを設置します。設定できるロールは各サーバー一つまでです。",
    )
    @app_commands.describe(
        role="認証が成功した際に付与するロール。",
        channel="認証パネルの送信先チャンネル。省略した場合現在のチャンネルに送信されます。",
        author="認証パネルに表示するユーザー。省略可。",
        title="認証パネルの見出し。省略可。",
        description="認証パネルに表示する文章。省略可。",
        button_text="認証ボタンに表示する言葉。省略可。",
    )
    @app_commands.allowed_contexts(guilds=True, dms=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def authPanelCommand(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        channel: discord.TextChannel = None,
        author: discord.User = None,
        title: str = "認証",
        description: str = "このサーバーを利用するには、認証が必要です！\n今すぐ「認証」ボタンを押して、認証を開始しましょう！",
        button_text: str = "認証する",
    ):
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
            await Database.pool.execute(
                "INSERT INTO guilds (id, role_id) VALUES ($1, $2)",
                interaction.guild.id,
                role.id,
            )
        else:
            await Database.pool.execute(
                "UPDATE ONLY guilds SET role_id = $2 WHERE id = $1",
                interaction.guild.id,
                role.id,
            )

        embed = discord.Embed(
            title=title, description=description, colour=discord.Colour.og_blurple()
        )
        if author is not None:
            embed.set_author(
                name=author.display_name, icon_url=author.display_avatar.url
            )
        if not channel:
            channel = interaction.channel

        if not channel.permissions_for(interaction.guild.me).send_messages:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description="<@1298239893608337440> に`メッセージを送信`する権限がありません。",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(ephemeral=True, embed=embed)
            return

        oauth2Url = os.getenv("oauth2_url")
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label=button_text, url=f"{oauth2Url}&state={interaction.guild.id}"
            )
        )
        await channel.send(embed=embed, view=view)
        embed = discord.Embed(title="✅認証パネルを送信しました！")
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(PanelCog(bot))
