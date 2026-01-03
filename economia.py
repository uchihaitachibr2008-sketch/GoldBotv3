import discord
from discord import app_commands
from discord.ext import commands

from database import pool, ensure_user


class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ===============================
    # SALDO
    # ===============================
    @app_commands.command(
        name="saldo",
        description="Veja seu saldo de moedas"
    )
    async def saldo(self, interaction: discord.Interaction):
        await ensure_user(interaction.user.id, interaction.user.name)

        async with pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT moedas FROM users WHERE user_id = $1",
                interaction.user.id
            )

        moedas = user["moedas"] if user else 0

        await interaction.response.send_message(
            f"💰 Seu saldo é **{moedas} moedas**",
            ephemeral=True
        )

    # ===============================
    # RANK
    # ===============================
    @app_commands.command(
        name="rank",
        description="Ranking dos jogadores mais ricos"
    )
    async def rank(self, interaction: discord.Interaction):
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT username, moedas
                FROM users
                ORDER BY moedas DESC
                LIMIT 10
            """)

        if not rows:
            await interaction.response.send_message(
                "📭 Ainda não há jogadores no ranking.",
                ephemeral=True
            )
            return

        texto = ""
        for i, row in enumerate(rows, start=1):
            texto += f"**{i}º** {row['username']} — 💰 {row['moedas']} moedas\n"

        embed = discord.Embed(
            title="🏆 Ranking de Moedas",
            description=texto,
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Economia(bot))
