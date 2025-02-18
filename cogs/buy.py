import random
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from .database import Database


class BuyCallPermWithPayPayModal(discord.ui.Modal, title="call権限をPayPayで購入"):
    def __init__(self, price: int):
        super().__init__()
        self.price = price

        self.serverIdStr = discord.ui.TextInput(
            label="サーバーID", placeholder="/serverid コマンドで確認できます"
        )
        self.add_item(self.serverIdStr)
        self.moneyUrl = discord.ui.TextInput(label="送金リンク")
        self.add_item(self.moneyUrl)
        self.passcord = discord.ui.TextInput(
            label="送金リンクのパスコード(設定した場合)",
            placeholder="設定していない場合は省略可能",
            max_length=4,
            required=False,
        )
        self.add_item(self.passcord)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        serverExists = await Database.pool.fetchval(
            "SELECT EXISTS (SELECT 1 FROM guilds WHERE id = $1)", self.serverIdStr.value
        )
        if not serverExists:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description="サーバーIDが間違っています",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        linkInfo = await Database.paypay.link_check(self.moneyUrl.value)
        if linkInfo.amount < self.price:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description="送金リンクの金額が足りません！",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await Database.pool.execute(
            """
                UPDATE guilds
                SET authorized_count = authorized_count + 10
                WHERE id = $1
            """,
            self.serverIdStr.value,
        )

        try:
            await Database.paypay.link_receive(
                self.moneyUrl.value, self.passcord.value, link_info=linkInfo
            )
        except Exception as e:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description=f"```{e}```",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="購入に成功しました",
            colour=discord.Colour.green(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


class BuyCallPermWithKyashModal(discord.ui.Modal, title="call権限をKyashで購入"):
    def __init__(self, price: int):
        super().__init__()
        self.price = price

        self.serverIdStr = discord.ui.TextInput(
            label="サーバーID", placeholder="/serverid コマンドで確認できます"
        )
        self.add_item(self.serverIdStr)
        self.moneyUrl = discord.ui.TextInput(label="送金リンク")
        self.add_item(self.moneyUrl)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        serverExists = await Database.pool.fetchval(
            "SELECT EXISTS (SELECT 1 FROM guilds WHERE id = $1)", self.serverIdStr.value
        )
        if not serverExists:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description="サーバーIDが間違っています",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        linkInfo = await Database.kyash.link_check(self.moneyUrl.value)
        if Database.kyash.link_amount < self.price:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description="送金リンクの金額が足りません！",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await Database.pool.execute(
            """
                UPDATE guilds
                SET authorized_count = authorized_count + 10
                WHERE id = $1
            """,
            self.serverIdStr.value,
        )

        try:
            await Database.kyash.link_recieve(self.moneyUrl.value, link_info=linkInfo)
        except Exception as e:
            embed = discord.Embed(
                title="⚠️エラーが発生しました",
                description=f"```{e}```",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="購入に成功しました",
            colour=discord.Colour.green(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


class BuyCallPermCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.already: bool = False

    @commands.Cog.listener()
    async def on_ready(self):
        if self.already:
            return

        channel: discord.TextChannel = self.bot.get_channel(1341354501365563503)
        messages: List[discord.Message] = [
            message async for message in channel.history()
        ]

        if len(messages) > 0:
            return

        await self.buyCallPermMessage()

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                await self.onButtonClick(interaction)
        except KeyError:
            pass

    async def onButtonClick(self, interaction: discord.Interaction):
        customId = interaction.data["custom_id"]
        customFields = customId.split(",")
        match customFields[0]:
            case "paypay":
                await interaction.response.send_modal(
                    BuyCallPermWithPayPayModal(int(customFields[1]))
                )
            case "kyash":
                await interaction.response.send_modal(
                    BuyCallPermWithKyashModal(int(customFields[1]))
                )
            case "reload":
                await interaction.response.defer(ephemeral=True)
                await self.buyCallPermMessage(message=interaction.message)
            case _:
                pass

    async def buyCallPermMessage(self, *, message: Optional[discord.Message] = None):
        count = await Database.pool.fetchval("SELECT COUNT(*) FROM users")
        if (count - 50) <= 0:
            minPrice = 0
        else:
            minPrice = count - 50
        price = random.randint(minPrice, count)
        embed = discord.Embed(
            title="call権限購入",
            description=f"認証済みユーザーを10人以上集められない場合や、一度10人集めたものの今すぐ/callを使いたい方はここからで購入できます\n現在の価格は**{price}円**です\n-# おつりは出てこないので気をつけてください",
            colour=discord.Colour.blurple(),
        )
        view = discord.ui.View(timeout=None)
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="PayPayで購入",
                custom_id=f"paypay,{price}",
                emoji=await self.bot.fetch_application_emoji(1341361847957458964),
            )
        )
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="Kyashで購入",
                custom_id=f"kyash,{price}",
                emoji=await self.bot.fetch_application_emoji(1341361810988601424),
            )
        )
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                custom_id=f"reload",
                emoji="🔃",
            )
        )
        if not message:
            channel: discord.TextChannel = self.bot.get_channel(1341354501365563503)
            await channel.send(embed=embed, view=view)
        else:
            await message.edit(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(BuyCallPermCog(bot))
