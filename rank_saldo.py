import discord
from discord.ext import commands
from discord import app_commands

from database import pool, ensure_user


class RankSaldo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # SALDO
    # =========================
    @app_commands.command(
        name="saldo",
        description="Ver suas moedas, vitórias, derrotas e streak"
    )
    async def saldo(self, interaction: discord.Interaction):
        await ensure_user(interaction.user.id, interaction.user.name)

        async with pool.acquire() as conn:
            user = await conn.fetchrow("""
                SELECT moedas, vitorias, derrotas,
                       streak_atual, streak_maximo
                FROM usuarios
                WHERE user_id = $1
            """, interaction.user.id)

        streak = user["streak_atual"]
        multiplicador = min(1.0 + (streak * 0.05), 1.20)

        embed = discord.Embed(
            title="💰 SEU SALDO",
            description=(
                f"👤 **Usuário:** {interaction.user.mention}\n\n"
                f"💰 **Moedas:** {user['moedas']}\n"
                f"🏆 **Vitórias:** {user['vitorias']}\n"
                f"💀 **Derrotas:** {user['derrotas']}\n\n"
                f"🔥 **Streak atual:** {streak}\n"
                f"⭐ **Streak máximo:** {user['streak_maximo']}\n"
                f"📈 **Multiplicador:** {multiplicador:.2f}x"
            ),
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    # =========================
    # RANK
    # =========================
    @app_commands.command(
        name="rank",
        description="Ver o ranking dos 10 melhores jogadores"
    )
    async def rank(self, interaction: discord.Interaction):
        async with pool.acquire() as conn:
            ranking = await conn.fetch("""
                SELECT user_id, vitorias, streak_atual
                FROM usuarios
                ORDER BY vitorias DESC, streak_atual DESC
                LIMIT 10
            """)

        if not ranking:
            await interaction.response.send_message(
                "❌ Ainda não há jogadores no ranking.",
                ephemeral=True
            )
            return

        descricao = ""
        for i, user in enumerate(ranking, start=1):
            descricao += (
                f"**{i}º** <@{user['user_id']}>\n"
                f"🏆 Vitórias: {user['vitorias']} | "
                f"🔥 Streak: {user['streak_atual']}\n\n"
            )

        embed = discord.Embed(
            title="🏆 RANKING GERAL",
            description=descricao,
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(RankSaldo(bot))
