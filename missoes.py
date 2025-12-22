import discord
from discord import app_commands
from discord.ext import commands
from datetime import date

from database import pool, ensure_user
from economia import add_coins, get_wallet

# ===============================
# CONFIGURAÇÕES
# ===============================

MISSOES = [
    # FÁCEIS
    {"id": 1, "desc": "Ganhe 1 x1", "reward": 5},
    {"id": 2, "desc": "Participe de 2 x1", "reward": 5},
    {"id": 3, "desc": "Use o comando /saldo", "reward": 3},
    {"id": 4, "desc": "Use o comando /rank", "reward": 3},
    {"id": 5, "desc": "Fique online por 1 hora", "reward": 5},

    # MÉDIAS
    {"id": 6, "desc": "Ganhe 3 x1", "reward": 10},
    {"id": 7, "desc": "Participe de 5 x1", "reward": 10},
    {"id": 8, "desc": "Chegue a streak 2", "reward": 12},
    {"id": 9, "desc": "Ganhe um x1 apostando 50 moedas", "reward": 15},

    # DIFÍCEIS
    {"id": 10, "desc": "Ganhe 5 x1", "reward": 20},
    {"id": 11, "desc": "Chegue a streak 3", "reward": 25},
    {"id": 12, "desc": "Ganhe um x1 com multiplicador ativo", "reward": 25},
    {"id": 13, "desc": "Complete uma caça com sucesso", "reward": 30},
]

# ===============================
# COG MISSÕES
# ===============================

class Missoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="missoes",
        description="Veja suas missões diárias e progresso"
    )
    async def missoes(self, interaction: discord.Interaction):
        await ensure_user(interaction.user.id, interaction.user.name)

        today = date.today()

        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT last_reset
                FROM missao_reset
                WHERE user_id = $1
            """, interaction.user.id)

            if not row or row["last_reset"] != today:
                await conn.execute("""
                    DELETE FROM missoes_usuarios
                    WHERE user_id = $1
                """, interaction.user.id)

                await conn.execute("""
                    INSERT INTO missao_reset (user_id, last_reset)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id)
                    DO UPDATE SET last_reset = $2
                """, interaction.user.id, today)

        async with pool.acquire() as conn:
            feitas = await conn.fetch("""
                SELECT mission_id
                FROM missoes_usuarios
                WHERE user_id = $1
            """, interaction.user.id)

        feitas_ids = {m["mission_id"] for m in feitas}

        embed = discord.Embed(
            title="📜 MISSÕES DIÁRIAS",
            description="Você pode completar **4 missões por dia**.\n"
                        "Cada missão só pode ser feita **1 vez**.\n\n",
            color=discord.Color.green()
        )

        count = 0
        for missao in MISSOES:
            if count >= 4:
                break

            status = "✅ Concluída" if missao["id"] in feitas_ids else "❌ Não feita"
            embed.add_field(
                name=f"{missao['desc']}",
                value=f"Recompensa: **{missao['reward']} moedas**\nStatus: {status}",
                inline=False
            )
            count += 1

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ===============================
    # COMANDO INTERNO PARA CONCLUIR MISSÃO
    # (chamado por outros sistemas)
    # ===============================

    async def completar_missao(self, user_id: int, mission_id: int):
        missao = next((m for m in MISSOES if m["id"] == mission_id), None)
        if not missao:
            return

        async with pool.acquire() as conn:
            feita = await conn.fetchrow("""
                SELECT 1 FROM missoes_usuarios
                WHERE user_id = $1 AND mission_id = $2
            """, user_id, mission_id)

            if feita:
                return

            total = await conn.fetchval("""
                SELECT COUNT(*) FROM missoes_usuarios
                WHERE user_id = $1
            """, user_id)

            if total >= 4:
                return

            await conn.execute("""
                INSERT INTO missoes_usuarios (user_id, mission_id)
                VALUES ($1, $2)
            """, user_id, mission_id)

        await add_coins(user_id, missao["reward"])


async def setup(bot):
    await bot.add_cog(Missoes(bot))
