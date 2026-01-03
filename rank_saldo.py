import discord
from discord.ext import commands
from discord import app_commands

from database import pool, ensure_user


class RankSaldo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ===============================
    # /saldo
    # ===============================
    @app_commands.command(
        name="saldo",
        description="Mostra seu saldo e estatísticas"
    )
    async def saldo(self, interaction: discord.Interaction):
        await ensure_user(interaction.user.id, interaction.user.name)

        async with pool.acquire() as conn:
            user = await conn.fetchrow("""
                SELECT moedas, vitorias, derrotas, streak_atual, streak_max
                FROM users
                WHERE user_id = $1
            """, interaction.user.id)

        if not user:
            await interaction.response.send_message(
                "❌ Usuário não encontrado.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="💰 Seu Saldo",
            color=discord.Color.green()
        )

        embed.add_field(name="🪙 Moedas", value=user["moedas"], inline=False)
        embed.add_field(
            name="⚔️ Vitórias / ❌ Derrotas",
            value=f'{user["vitorias"]} / {user["derrotas"]}',
            inline=False
        )
        embed.add_field(name="🔥 Streak Atual", value=user["streak_atual"], inline=True)
        embed.add_field(name="🏆 Streak Máximo", value=user["streak_max"], inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ===============================
    # /rank
    # ===============================
    @app_commands.command(
        name="rank",
        description="Ranking dos 10 jogadores com mais vitórias"
    )
    async def rank(self, interaction: discord.Interaction):
        async with pool.acquire() as conn:
            ranking = await conn.fetch("""
                SELECT user_id, vitorias, streak_atual
                FROM users
                ORDER BY vitorias DESC
                LIMIT 10
            """)

        if not ranking:
            await interaction.response.send_message(
                "❌ Ainda não há dados para o ranking.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🏆 Ranking de Vitórias",
            color=discord.Color.gold()
        )

        for posicao, user in enumerate(ranking, start=1):
            member = self.bot.get_user(user["user_id"])
            nome = member.name if member else f'Usuário {user["user_id"]}'

            embed.add_field(
                name=f"#{posicao} - {nome}",
                value=(
                    f"⚔️ Vitórias: {user['vitorias']}\n"
                    f"🔥 Streak Atual: {user['streak_atual']}"
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(RankSaldo(bot))
