import discord
from discord import app_commands
from discord.ext import commands

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
        user_id = interaction.user.id

        user = await get_user(user_id)

        if not user:
            await interaction.response.send_message(
                "❌ Você ainda não possui registro no sistema.",
                ephemeral=True
            )
            return

        moedas = user["moedas"]
        vitorias = user["vitorias"]
        derrotas = user["derrotas"]
        streak_atual = user["streak_atual"]
        streak_max = user["streak_max"]
        multiplicador = user["multiplicador"]

        embed = discord.Embed(
            title="💰 Seu saldo",
            color=discord.Color.green()
        )

        embed.add_field(
            name="🪙 Moedas",
            value=f"{moedas}",
            inline=False
        )

        embed.add_field(
            name="⚔️ Vitórias / ❌ Derrotas",
            value=f"{vitorias} / {derrotas}",
            inline=False
        )

        embed.add_field(
            name="🔥 Streak atual",
            value=f"{streak_atual}",
            inline=True
        )

        embed.add_field(
            name="🏆 Streak máximo",
            value=f"{streak_max}",
            inline=True
        )

        embed.add_field(
            name="📈 Multiplicador",
            value=f"{multiplicador}x",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ===============================
    # /rank
    # ===============================
    @app_commands.command(
        name="rank",
        description="Mostra o ranking dos 10 melhores jogadores"
    )
    async def rank(self, interaction: discord.Interaction):
        top_users = await get_top_users()

        if not top_users:
            await interaction.response.send_message(
                "❌ Ainda não há jogadores no ranking.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🏆 Ranking de Vitórias",
            description="Top 10 jogadores do servidor",
            color=discord.Color.gold()
        )

        for posicao, user in enumerate(top_users, start=1):
            user_id = user["user_id"]
            vitorias = user["vitorias"]
            streak = user["streak_atual"]

            try:
                member = await self.bot.fetch_user(user_id)
                nome = member.name
            except:
                nome = f"Usuário {user_id}"

            embed.add_field(
                name=f"#{posicao} - {nome}",
                value=f"⚔️ Vitórias: {vitorias}\n🔥 Streak: {streak}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)


# ===============================
# SETUP OBRIGATÓRIO
# ===============================
async def setup(bot: commands.Bot):
    await bot.add_cog(RankSaldo(bot))
