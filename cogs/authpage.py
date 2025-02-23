import os
import traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
import dotenv
from discord.ext import commands
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient

from .database import Database

dotenv.load_dotenv()
templates = Jinja2Templates(directory="pages")


class AuthPageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = AsyncClient()

    async def discordCallback(self, request: Request, code: str, state: int):
        try:
            guild = self.bot.get_guild(state)
            row = await Database.pool.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", guild.id
            )
            if not row:
                return templates.TemplateResponse(
                    request=request,
                    name="auth_error.html",
                    context={
                        "message": "認証しようとしたサーバーではまだnyaが設定されていません"
                    },
                    status_code=403,
                )
            role = guild.get_role(row["role_id"])
            response = await self.client.post(
                "https://discord.com/api/oauth2/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_id": os.getenv("oauth2_client_id"),
                    "client_secret": os.getenv("oauth2_secret"),
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": os.getenv("redirect_uri"),
                },
            )
            if response.status_code != 200:
                return templates.TemplateResponse(
                    request=request,
                    name="auth_error.html",
                    context={
                        "message": f"oauth2の検証に失敗しました。code: {response.status_code}"
                    },
                    status_code=403,
                )
            accessTokenResponse = response.json()
            print(accessTokenResponse)
            if ("guilds.join" in accessTokenResponse["scope"]) and (
                "identify" in accessTokenResponse["scope"]
            ):
                accessToken = accessTokenResponse["access_token"]

                response = await self.client.get(
                    "https://discord.com/api/v10/users/@me",
                    headers={"Authorization": f"Bearer {accessToken}"},
                )
                if response.status_code != 200:
                    return templates.TemplateResponse(
                        request=request,
                        name="auth_error.html",
                        context={
                            "message": f"ユーザーデータの取得に失敗しました。code: {response.status_code}"
                        },
                        status_code=403,
                    )
                userData = response.json()
                user = await guild.fetch_member(int(userData["id"]))
                await user.add_roles(role, reason="認証に成功したため。")
                refreshToken = accessTokenResponse["refresh_token"]
                expiresAt = datetime.now() + timedelta(
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
                    user.id,
                    accessToken,
                    refreshToken,
                    expiresAt,
                )

                await Database.pool.execute(
                    """
                        UPDATE guilds
                        SET authorized_members = ARRAY(SELECT DISTINCT unnest(authorized_members) UNION ALL SELECT $2),
                            authorized_count = authorized_count + 1
                        WHERE id = $1
                        AND NOT ($2 = ANY(authorized_members));
                    """,
                    guild.id,
                    user.id,
                )

                return templates.TemplateResponse(
                    request=request,
                    name="authorized.html",
                    context={"user": user, "guild": guild},
                )
            else:
                raise HTTPException(status_code=403)
        except Exception as e:
            traceback.print_exc()
            return templates.TemplateResponse(
                request=request,
                name="auth_error.html",
                context={"message": str(e)},
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(AuthPageCog(bot))
