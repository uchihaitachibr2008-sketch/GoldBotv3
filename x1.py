import discord
from discord import app_commands
from discord.ext import commands

from database import pool, ensure_user
from economia import add_coins, remove_coins
from config import ADM_ID, TAXA_ADM_X1, CANAL_X1_HISTORICO_ID


# ===============================
# VIEW DESAFIO
# ===============================
class DesafioView(discord.ui.View):
    def __init__(self, autor, alvo, valor):
        super().__init__(timeout=120)
        self.autor = autor
        self.alvo = alvo
        self.valor = valor
        self.aceito = False

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.alvo.id:
            await interaction.response.send_message(
                "❌ Apenas o desafiado pode aceitar.",
                ephemeral=True
            )
            return

        self.aceito = True
        self.stop()
        await interaction.response.send_message("✅ Desafio aceito!", ephemeral=True)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.alvo.id:
            await interaction.response.send_message(
                "❌ Apenas o desafiado pode recusar.",
                ephemeral=True
            )
            return

        self.stop()
        await interaction.response.send_message("❌ Desafio recusado.", ephemeral=True)


# ===============================
# COG X1
# ===============================
class X1(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------- DESAFIAR --------
    @app_commands.command(
        name="x1",
        description="Desafie um jogador para um x1 apostando moedas"
    )
    async def x1(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        valor: int
    ):
        if usuario.bot or usuario.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Usuário inválido.",
                ephemeral=True
            )
            return

        if valor <= 0:
            await interaction.response.send_message(
                "❌ Valor inválido.",
                ephemeral=True
            )
            return

        await ensure_user(interaction.user.id, interaction.user.name)
        await ensure_user(usuario.id, usuario.name)

        async with pool.acquire() as conn:
            saldo1 = await conn.fetchval(
                "SELECT moedas FROM users WHERE user_id = $1",
                interaction.user.id
            )
            saldo2 = await conn.fetchval(
                "SELECT moedas FROM users WHERE user_id = $1",
                usuario.id
            )

        if saldo1 < valor or saldo2 < valor:
            await interaction.response.send_message(
                "❌ Um dos jogadores não possui saldo suficiente.",
                ephemeral=True
            )
            return

        view = DesafioView(interaction.user, usuario, valor)

        await interaction.response.send_message(
            f"⚔️ **DESAFIO DE X1**\n\n"
            f"{interaction.user.mention} desafiou {usuario.mention}\n"
            f"💰 Valor: **{valor} moedas**\n"
            f"🏦 Taxa ADM: **{int(TAXA_ADM_X1 * 100)}%**",
            view=view
        )

        await view.wait()
        if not view.aceito:
            return

        # Remove moedas dos dois
        await remove_coins(interaction.user.id, valor)
        await remove_coins(usuario.id, valor)

        async with pool.acquire() as conn:
            match_id = await conn.fetchval("""
                INSERT INTO x1 (jogador1, jogador2, valor, status)
                VALUES ($1, $2, $3, 'ativo')
                RETURNING id
            """, interaction.user.id, usuario.id, valor)

        await interaction.followup.send(
            f"🔥 X1 iniciado com ID **#{match_id}**!\n"
            f"O ADM deve usar `/confirmarx1 {match_id} vencedor`",
            ephemeral=True
        )

    # -------- CONFIRMAR (ADM) --------
    @app_commands.command(
        name="confirmarx1",
        description="(ADM) Confirmar vencedor de um x1"
    )
    async def confirmarx1(
        self,
        interaction: discord.Interaction,
        id: int,
        vencedor: discord.Member
    ):
        if interaction.user.id != ADM_ID:
            await interaction.response.send_message(
                "❌ Apenas o ADM pode confirmar.",
                ephemeral=True
            )
            return

        async with pool.acquire() as conn:
            x1 = await conn.fetchrow(
                "SELECT
