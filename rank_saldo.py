import discord
from discord.ext import commands
from discord import app_commands

from database import get_user, get_top_users


class RankSaldo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ===============================
    # /saldo
    # ===============================
    @app_commands.command(
        name="saldo",
        description="Mostra seu saldo, vitórias, derrotas e streak"
    )
    async def saldo(self, interaction: discord.Interaction):
        user = await get_user(interaction.user.id)

        if not user:
            await interaction.response.send_message(
                "❌ Você ainda não possui registro no sistema.",
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
        embed.add_field(
            name="📈 Multiplicador",
            value=f'{user["multiplicador"]}x',
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ===============================
    # /rank
    # ===============================
    @app_commands.command(
        name="rank",
        description="Mostra o ranking dos 10 jogadores com mais vitórias"
    )
    async def rank(self, interaction: discord.Interaction):
        ranking = await get_top_users()

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
            try:
                member = await self.bot.fetch_user(user["user_id"])
                nome = member.name
            except:
                nome = f'Usuário {user["user_id"]}'

            embed.add_field(
                name=f"#{posicao} - {nome}",
                value=f'⚔️ Vitórias: {user["vitorias"]}\n🔥 Streak: {user["streak_atual"]}',
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(RankSaldo(bot))
