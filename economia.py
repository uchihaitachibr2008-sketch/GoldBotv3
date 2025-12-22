import discord
from discord import app_commands
from discord.ext import commands

from database import pool, ensure_user
from config import (
    ADM_ID,
    STREAK_INICIO,
    STREAK_MULTIPLICADORES,
    STREAK_RECOMPENSA_CACA
)

# ===============================
# FUNÇÕES INTERNAS
# ===============================

async def get_wallet(user_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT coins FROM wallet WHERE user_id = $1",
            user_id
        )
        return row["coins"] if row else 0


async def add_coins(user_id: int, amount: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE wallet SET coins = coins + $1 WHERE user_id = $2",
            amount, user_id
        )


async def remove_coins(user_id: int, amount: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE wallet SET coins = coins - $1 WHERE user_id = $2 AND coins >= $1",
            amount, user_id
        )


async def register_win(user_id: int):
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT wins, streak, max_streak FROM users WHERE user_id = $1",
            user_id
        )

        wins = user["wins"] + 1
        streak = user["streak"] + 1
        max_streak = max(user["max_streak"], streak)

        await conn.execute("""
            UPDATE users
            SET wins = $1, streak = $2, max_streak = $3
            WHERE user_id = $4
        """, wins, streak, max_streak, user_id)

        await update_streak_data(user_id, streak)


async def register_loss(user_id: int):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users
            SET losses = losses + 1, streak = 0
            WHERE user_id = $1
        """, user_id)

        await conn.execute("""
            UPDATE streaks
            SET multiplier = 1.0, hunt_reward = 0, active = FALSE
            WHERE user_id = $1
        """, user_id)


async def update_streak_data(user_id: int, streak: int):
    if streak < STREAK_INICIO:
        return

    multiplier = STREAK_MULTIPLICADORES.get(streak, 1.20)
    reward = STREAK_RECOMPENSA_CACA.get(streak, 0)

    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE streaks
            SET multiplier = $1,
                hunt_reward = $2,
                active = TRUE
            WHERE user_id = $3
        """, multiplier, reward, user_id)


async def get_streak_data(user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM streaks WHERE user_id = $1",
            user_id
        )


# ===============================
# COG DE ECONOMIA
# ===============================

class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------- SALDO --------
    @app_commands.command(
        name="saldo",
        description="Veja seu saldo, vitórias, derrotas e streak"
    )
    async def saldo(self, interaction: discord.Interaction):
        await ensure_user(interaction.user.id, interaction.user.name)

        async with pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                interaction.user.id
            )

        coins = await get_wallet(interaction.user.id)
        streak_data = await get_streak_data(interaction.user.id)

        embed = discord.Embed(
            title="💰 Seu Saldo",
            color=discord.Color.green()
        )

        embed.add_field(name="Moedas", value=f"{coins}", inline=True)
        embed.add_field(name="Vitórias", value=f"{user['wins']}", inline=True)
        embed.add_field(name="Derrotas", value=f"{user['losses']}", inline=True)

        embed.add_field(
            name="Streak Atual",
            value=f"{user['streak']}",
            inline=True
        )
        embed.add_field(
            name="Streak Máximo",
            value=f"{user['max_streak']}",
            inline=True
        )
        embed.add_field(
            name="Multiplicador",
            value=f"{streak_data['multiplier']}x",
            inline=True
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------- RANK --------
    @app_commands.command(
        name="rank",
        description="Veja o rank dos 10 melhores jogadores"
    )
    async def rank(self, interaction: discord.Interaction):
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT username, wins, streak
                FROM users
                ORDER BY wins DESC
                LIMIT 10
            """)

        embed = discord.Embed(
            title="🏆 Rank Top 10",
            color=discord.Color.gold()
        )

        for i, row in enumerate(rows, start=1):
            embed.add_field(
                name=f"{i}º {row['username']}",
                value=f"Vitórias: {row['wins']} | Streak: {row['streak']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    # -------- MOEDAS (ADM) --------
    @app_commands.command(
        name="moedas",
        description="Adicionar ou remover moedas de um usuário (ADM)"
    )
    @app_commands.describe(
        acao="adicionar ou tirar",
        usuario="Usuário alvo",
        valor="Quantidade de moedas"
    )
    async def moedas(
        self,
        interaction: discord.Interaction,
        acao: str,
        usuario: discord.Member,
        valor: int
    ):
        if interaction.user.id != ADM_ID:
            await interaction.response.send_message(
                "❌ Apenas o ADM pode usar esse comando.",
                ephemeral=True
            )
            return

        await ensure_user(usuario.id, usuario.name)

        if valor <= 0:
            await interaction.response.send_message(
                "❌ Valor inválido.",
                ephemeral=True
            )
            return

        if acao.lower() == "adicionar":
            await add_coins(usuario.id, valor)
            msg = f"✅ {valor} moedas adicionadas para {usuario.mention}"

        elif acao.lower() == "tirar":
            await remove_coins(usuario.id, valor)
            msg = f"✅ {valor} moedas removidas de {usuario.mention}"

        else:
            msg = "❌ Ação inválida. Use adicionar ou tirar."

        await interaction.response.send_message(msg)


# ===============================
# SETUP
# ===============================

async def setup(bot):
    await bot.add_cog(Economia(bot))
