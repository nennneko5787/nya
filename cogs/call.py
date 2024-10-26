import asyncio
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import discord
import dotenv
from discord import app_commands
from discord.ext import commands
from httpx import AsyncClient

from .database import Database

dotenv.load_dotenv()


class CallCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = AsyncClient()

    @app_commands.command(name="call", description='認証した人"全員"を追加')
    @app_commands.describe(
        ephemeral="他のユーザーに追加していることを報告するかどうか。",
    )
    @app_commands.allowed_contexts(guilds=True, dms=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def callCommand(
        self, interaction: discord.Interaction, ephemeral: bool = True
    ):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description="あなたはこのコマンドを実行する権限を持ってません！",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(ephemeral=True, embed=embed)
            return
        await interaction.response.defer(ephemeral=ephemeral)
        row = await Database.pool.fetchrow(
            "SELECT * FROM guilds WHERE id = $1", interaction.guild.id
        )
        if not row:
            embed = discord.Embed(
                title=f"⚠️エラーが発生しました",
                description=f"まだ認証パネルを設置していないようです！\n`/authpanel` コマンドを使用して、認証パネルを設置してください。",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
            return
        if row["authorized_count"] < 10:
            embed = discord.Embed(
                title=f"⚠️エラーが発生しました",
                description="最後の`/call`から10人以上認証しないと、`/call`は使用することができません。\n10人以上集められない場合は、**[サポートサーバー](https://discord.gg/2TfFUuY3RG)**で`/call`の使用権を購入することができます。",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
            return

        await Database.pool.execute(
            """
                UPDATE guilds
                SET authorized_count = authorized_count - 10
                WHERE id = $1
            """,
            interaction.guild.id,
        )

        embed = discord.Embed(
            title="call開始",
            description="```callを開始しました...```",
            colour=discord.Colour.og_blurple(),
        )
        await interaction.followup.send(embed=embed, ephemeral=ephemeral)

        addedCount = 0
        alreadyAddedCount = 0
        failedToRefreshCount = 0
        userUnlinkedCount = 0
        catchGuildLimit = 0
        accountDeletedCount = 0
        otherReasonCount = 0

        users = await Database.pool.fetch("SELECT * FROM users ORDER BY created_at DESC")
        for user in users:
            print(user)
            token: str = user["token"]
            refreshToken: str = user["refresh_token"]
            expiresAt: datetime = user["expires_at"]
            if datetime.now().timestamp() > expiresAt.timestamp():
                response = await self.client.post(
                    "https://discord.com/api/oauth2/token",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "client_id": os.getenv("oauth2_client_id"),
                        "client_secret": os.getenv("oauth2_secret"),
                        "grant_type": "refresh_token",
                        "refresh_token": refreshToken,
                    },
                )
                if response.status_code != 200:
                    failedToRefreshCount += 1
                    continue
                accessTokenResponse = response.json()
                token: str = accessTokenResponse["access_token"]
                refreshToken: str = user["refresh_token"]
                expiresAt = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(
                    seconds=accessTokenResponse["expires_in"]
                )

                await Database.pool.execute(
                    """
                        INSERT INTO users (id, token, refresh_token, expires_at)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (id) 
                        DO UPDATE SET 
                            token = EXCLUDED.token,
                            refresh_token = EXCLUDED.refresh_token,
                            expires_at = EXCLUDED.expires_at;
                    """,
                    user["id"],
                    token,
                    refreshToken,
                    expiresAt,
                )

            while True:
                response = await self.client.put(
                    f"https://discord.com/api/v10/guilds/{interaction.guild.id}/members/{user['id']}",
                    headers={
                        "Authorization": f"Bot {os.getenv('discord')}",
                        "Content-Type": "application/json",
                    },
                    json={"access_token": token},
                )
                match response.status_code:
                    case 201:
                        addedCount += 1
                        break
                    case 204:
                        alreadyAddedCount += 1
                        break
                    case 400:
                        catchGuildLimit += 1
                        break
                    case 403:
                        userUnlinkedCount += 1
                        await Database.pool.execute(
                            """
                                DELETE FROM users WHERE id = $1
                            """,
                            user["id"],
                        )
                        break
                    case 404:
                        accountDeletedCount += 1
                        await Database.pool.execute(
                            """
                                DELETE FROM users WHERE id = $1
                            """,
                            user["id"],
                        )
                        break
                    case 429:
                        await asyncio.sleep(int(response.headers["Retry-After"]))
                        continue
                    case statusCode:
                        print(statusCode)
                        otherReasonCount += 1
                        break
        embed = discord.Embed(
            title="call終了",
            description=f"【結果】\n追加できた数: {addedCount}\nすでに追加されていた数: {alreadyAddedCount}\nトークンのリフレッシュに失敗した数: {failedToRefreshCount}\nアプリ連携が解除された数: {userUnlinkedCount}\n最大サーバー数(100または200)を超えようとした数: {catchGuildLimit}\nアカウントが削除された数: {accountDeletedCount}\nその他の理由: {otherReasonCount}",
        )
        await interaction.followup.send(embed=embed, ephemeral=ephemeral)


async def setup(bot: commands.Bot):
    await bot.add_cog(CallCog(bot))
