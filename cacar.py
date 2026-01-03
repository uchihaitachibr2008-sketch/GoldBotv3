import discord
from discord.ext import commands
from discord import app_commands
import random

from economia import add_coins
from database import pool

# ===============================
# CONFIGURAÇÕES
# ===============================

GUILD_ID = 1447592173913509919
ADM_ID = 969976402571063397
CANAL_HISTORICO_CACA = 1451350066416582657


class Caca(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="cacar",
        description="(ADM) Inicia um evento de caça no servidor"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def cacar(
        self,
        interaction: discord.Interaction,
        recompensa: int
    ):
        if interaction.user.id != ADM_ID:
            await interaction.response.send_message(
                "❌ Apenas o ADM pode usar este comando.",
                ephemeral=True
            )
            return

        if recompensa <= 0:
            await interaction.response.send_message(
                "❌ Recompensa inválida.",
                ephemeral=True
            )
            return

        guild = interaction.guild

        online_members = [
            m for m in guild.members
            if not m.bot and m.status != discord.Status.offline
        ]

        if not online_members:
            await interaction.response.send_message(
                "❌ Nenhum usuário online para caçar.",
                ephemeral=True
            )
            return

        alvo = random.choice(online_members)

        async with pool.acquire() as conn:
            ativo = await conn.fetchrow(
                "SELECT 1 FROM cacas WHERE ativo = true"
            )
            if ativo:
                await interaction.response.send_message(
                    "⚠️ Já existe uma caça ativa.",
                    ephemeral=True
                )
                return

            await conn.execute(
                """
                INSERT INTO cacas (alvo_id, recompensa, derrotas, ativo)
                VALUES ($1, $2, 0, true)
                """,
                alvo.id,
                recompensa
            )

        embed = discord.Embed(
            title="🏹 EVENTO DE CAÇA INICIADO!",
            description=(
                f"🎯 **Alvo:** {alvo.mention}\n"
                f"💰 **Recompensa:** {recompensa} moedas\n\n"
                "⚔️ Se esse jogador for derrotado em um **X1**, "
                "o vencedor recebe a recompensa imediatamente.\n\n"
                "🛡️ Caso o alvo **sobreviva a 3 X1**, ele vence o evento!"
            ),
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed)

    # ===============================
    # FUNÇÕES AUXILIARES
    # ===============================

    async def registrar_derrota(self, alvo_id: int, vencedor_id: int):
        async with pool.acquire() as conn:
            caca = await conn.fetchrow(
                """
                SELECT * FROM cacas
                WHERE ativo = true AND alvo_id = $1
                """,
                alvo_id
            )

            if not caca:
                return False

            await add_coins(vencedor_id, caca["recompensa"])

            await conn.execute(
                "UPDATE cacas SET ativo = false WHERE alvo_id = $1",
                alvo_id
            )

        canal = self.bot.get_channel(CANAL_HISTORICO_CACA)
        if canal:
            await canal.send(
                f"🏹 **CAÇA FINALIZADA!**\n"
                f"🎯 Alvo: <@{alvo_id}>\n"
                f"🏆 Vencedor: <@{vencedor_id}>\n"
                f"💰 Recompensa: {caca['recompensa']} moedas"
            )

        return True

    async def registrar_sobrevivencia(self, alvo_id: int):
        async with pool.acquire() as conn:
            caca = await conn.fetchrow(
                """
                SELECT * FROM cacas
                WHERE ativo = true AND alvo_id = $1
                """,
                alvo_id
            )

            if not caca:
                return

            derrotas = caca["derrotas"] + 1

            if derrotas >= 3:
                await conn.execute(
                    "UPDATE cacas SET ativo = false WHERE alvo_id = $1",
                    alvo_id
                )

                canal = self.bot.get_channel(CANAL_HISTORICO_CACA)
                if canal:
                    await canal.send(
                        f"🛡️ **CAÇA ENCERRADA!**\n"
                        f"O alvo <@{alvo_id}> sobreviveu a 3 X1!"
                    )
            else:
                await conn.execute(
                    """
                    UPDATE cacas
                    SET derrotas = $2
                    WHERE alvo_id = $1
                    """,
                    alvo_id,
                    derrotas
                )


async def setup(bot):
    await bot.add_cog(Caca(bot))
