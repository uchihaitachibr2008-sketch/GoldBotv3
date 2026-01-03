import discord
from discord import app_commands
from discord.ext import commands
from datetime import date

from database import pool, ensure_user
from economia import add_coins

# ===============================
# MISSÕES DISPONÍVEIS
# ===============================

MISSOES = [
    {"id": 1, "desc": "Ganhe 1 X1", "reward": 5},
    {"id": 2, "desc": "Participe de 2 X1", "reward": 5},
    {"id": 3, "desc": "Use o comando /saldo", "reward": 3},
    {"id": 4, "desc": "Use o comando /rank", "reward": 3},
    {"id": 5, "desc": "Fique online por 1 hora", "reward": 5},
    {"id": 6, "desc": "Ganhe 3 X1", "reward": 10},
    {"id": 7, "desc": "Chegue a streak 2", "reward": 12},
    {"id": 8, "desc": "Ganhe um X1 apostando 50 moedas", "reward": 15},
    {"id": 9, "desc": "Ganhe 5 X1", "reward": 20},
    {"id": 10, "desc": "Complete uma caça", "reward": 30},
]

MAX_MISSOES_DIA = 4

# ===============================
# COG
# ===============================

class Missoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="missoes",
        description="Veja suas missões diárias"
    )
    async def missoes(self, interaction: discord.Interaction):
        await ensure_user(interaction.user.id, interaction.user.name)

        hoje = date.today()

        async with pool.acquire() as conn:
            feitas = await conn.fetch("""
                SELECT missao
                FROM missoes
                WHERE user_id = $1 AND data = $2
            """, interaction.user.id, hoje)

        feitas_ids = {row["missao"] for row in feitas}

        embed = discord.Embed(
            title="📜 Missões Diárias",
            description=f"Você pode concluir até **{MAX_MISSOES_DIA} missões por dia**.\n",
            color=discord.Color.green()
        )

        for missao in MISSOES[:MAX_MISSOES_DIA]:
            status = "✅ Concluída" if missao["id"] in feitas_ids else "❌ Não concluída"

            embed.add_field(
                name=missao["desc"],
                value=f"💰 Recompensa: **{missao['reward']} moedas**\n{status}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ===============================
    # FUNÇÃO INTERNA (CHAMADA POR OUTROS COGS)
    # ===============================

    async def completar_missao(self, user_id: int, missao_id: int):
        hoje = date.today()

        async with pool.acquire() as conn:
            total = await conn.fetchval("""
                SELECT COUNT(*)
                FROM missoes
                WHERE user_id = $1 AND data = $2
            """, user_id, hoje)

            if total >= MAX_MISSOES_DIA:
                return

            feita = await conn.fetchrow("""
                SELECT 1 FROM missoes
                WHERE user_id = $1 AND missao = $2 AND data = $3
            """, user_id, missao_id, hoje)

            if feita:
                return

            await conn.execute("""
                INSERT INTO missoes (user_id, missao, concluida, data)
                VALUES ($1, $2, TRUE, $3)
            """, user_id, missao_id, hoje)

        missao = next((m for m in MISSOES if m["id"] == missao_id), None)
        if missao:
            await add_coins(user_id, missao["reward"])


async def setup(bot):
    await bot.add_cog(Missoes(bot))
