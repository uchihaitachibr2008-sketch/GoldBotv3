import discord
from discord import app_commands
from discord.ext import commands

from database import pool, ensure_user
from config import ADM_ID

GUILD_ID = 1447592173913509919


class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------- SALDO --------
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="saldo",
        description="Veja seu saldo"
    )
    async def saldo(self, interaction: discord.Interaction):
        await ensure_user(interaction.user.id, interaction.user.name)

        async with pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT coins FROM wallet WHERE user_id = $1",
                interaction.user.id
            )

        coins = user["coins"] if user else 0

        await interaction.response.send_message(
            f"💰 Seu saldo é **{coins} moedas**",
            ephemeral=True
        )

    # -------- RANK --------
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="rank",
        description="Rank dos jogadores"
    )
    async def rank(self, interaction: discord.Interaction):
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT username, coins
                FROM wallet
                ORDER BY coins DESC
                LIMIT 10
            """)

        if not rows:
            await interaction.response.send_message("Nenhum dado ainda.")
            return

        texto = ""
        for i, row in enumerate(rows, start=1):
            texto += f"{i}º **{row['username']}** — {row['coins']} moedas\n"

        embed = discord.Embed(
            title="🏆 Rank de Moedas",
            description=texto,
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Economia(bot))
