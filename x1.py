import discord
from discord import app_commands
from discord.ext import commands

from database import pool, ensure_user
from economia import (
    get_wallet,
    add_coins,
    remove_coins,
    register_win,
    register_loss,
    get_streak_data
)
from config import (
    ADM_ID,
    TAXA_ADM_X1,
    CANAL_X1_HISTORICO_ID,
    STREAK_VALOR_MINIMO_DESAFIO
)

# ===============================
# VIEWS
# ===============================

class DesafioView(discord.ui.View):
    def __init__(self, challenger, opponent, value):
        super().__init__(timeout=300)
        self.challenger = challenger
        self.opponent = opponent
        self.value = value
        self.accepted = False

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message(
                "❌ Apenas o desafiado pode aceitar.",
                ephemeral=True
            )
            return

        self.accepted = True
        self.stop()
        await interaction.response.send_message("✅ Desafio aceito!")

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message(
                "❌ Apenas o desafiado pode recusar.",
                ephemeral=True
            )
            return

        self.stop()
        await interaction.response.send_message("❌ Desafio recusado.")


class VotacaoView(discord.ui.View):
    def __init__(self, match_id, p1, p2):
        super().__init__(timeout=None)
        self.match_id = match_id
        self.p1 = p1
        self.p2 = p2
        self.votes = {}

    async def register_vote(self, interaction, voted_id):
        if interaction.user.id not in (self.p1.id, self.p2.id):
            await interaction.response.send_message(
                "❌ Você não participa deste x1.",
                ephemeral=True
            )
            return

        self.votes[interaction.user.id] = voted_id

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO x1_votes (match_id, voter_id, voted_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (match_id, voter_id)
                DO UPDATE SET voted_id = $3
            """, self.match_id, interaction.user.id, voted_id)

        await interaction.response.send_message("🗳️ Voto registrado.", ephemeral=True)

    @discord.ui.button(label="Jogador 1", style=discord.ButtonStyle.primary)
    async def voto_p1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, self.p1.id)

    @discord.ui.button(label="Jogador 2", style=discord.ButtonStyle.primary)
    async def voto_p2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, self.p2.id)

# ===============================
# COG X1
# ===============================

class X1(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------- DESAFIO --------
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

        saldo1 = await get_wallet(interaction.user.id)
        saldo2 = await get_wallet(usuario.id)

        if saldo1 < valor or saldo2 < valor:
            await interaction.response.send_message(
                "❌ Um dos jogadores não possui saldo suficiente.",
                ephemeral=True
            )
            return

        streak_data = await get_streak_data(usuario.id)
        if streak_data["active"]:
            min_val = STREAK_VALOR_MINIMO_DESAFIO.get(
                int(streak_data["multiplier"] * 10) - 10, 0
            )
            if valor < min_val:
                await interaction.response.send_message(
                    f"❌ Para desafiar esse jogador o mínimo é {min_val} moedas.",
                    ephemeral=True
                )
                return

        view = DesafioView(interaction.user, usuario, valor)

        await interaction.response.send_message(
            f"⚔️ **Desafio de X1**\n\n"
            f"{interaction.user.mention} desafiou {usuario.mention}\n"
            f"💰 Valor: **{valor} moedas**\n"
            f"🏦 Taxa ADM: **25%**\n\n"
            f"Escolha aceitar ou recusar:",
            view=view
        )

        await view.wait()

        if not view.accepted:
            return

        # CRIA X1
        async with pool.acquire() as conn:
            match_id = await conn.fetchval("""
                INSERT INTO x1_matches (challenger, opponent, value, status)
                VALUES ($1, $2, $3, 'ativo')
                RETURNING id
            """, interaction.user.id, usuario.id, valor)

        guild = interaction.guild

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            usuario: discord.PermissionOverwrite(view_channel=True),
            guild.get_member(ADM_ID): discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            name=f"x1-{match_id}",
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="⚔️ X1 INICIADO",
            description=(
                f"Valor apostado: **{valor} moedas**\n"
                f"Taxa ADM: **25%**\n\n"
                f"🗳️ Ambos devem votar no vencedor."
            ),
            color=discord.Color.orange()
        )

        view_vote = VotacaoView(match_id, interaction.user, usuario)

        await channel.send(embed=embed, view=view_vote)

    # -------- CONFIRMAR X1 (ADM) --------
    @app_commands.command(
        name="confirmarx1",
        description="Confirmar vencedor de um x1 (ADM)"
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
            match = await conn.fetchrow(
                "SELECT * FROM x1_matches WHERE id = $1 AND status = 'ativo'",
                id
            )

            if not match:
                await interaction.response.send_message(
                    "❌ X1 não encontrado ou já finalizado.",
                    ephemeral=True
                )
                return

            valor = match["value"]
            total = valor * 2
            taxa = int(total * TAXA_ADM_X1)
            premio_base = total - taxa

            streak = await get_streak_data(vencedor.id)
            premio_final = int(premio_base * streak["multiplier"])

            await add_coins(vencedor.id, premio_final)
            await add_coins(ADM_ID, taxa)

            await register_win(vencedor.id)

            perdedor = match["opponent"] if vencedor.id == match["challenger"] else match["challenger"]
            await register_loss(perdedor)

            await conn.execute("""
                UPDATE x1_matches
                SET status = 'finalizado', winner = $1, admin_fee = $2
                WHERE id = $3
            """, vencedor.id, taxa, id)

        canal = interaction.guild.get_channel(CANAL_X1_HISTORICO_ID)
        if canal:
            await canal.send(
                f"🏆 X1 #{id} finalizado!\n"
                f"Vencedor: {vencedor.mention}\n"
                f"Prêmio: {premio_final} moedas"
            )

        await interaction.response.send_message(
            f"✅ X1 #{id} confirmado.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(X1(bot))
