import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from economia import remove_coins
from database import pool, ensure_user

ADM_ID = 969976402571063397
CANAL_HISTORICO_SAQUE = 1451350213146181703


class Saque(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ===============================
    # /saque
    # ===============================
    @app_commands.command(
        name="saque",
        description="Solicitar saque de moedas (1 moeda = R$ 0,10)"
    )
    async def saque(
        self,
        interaction: discord.Interaction,
        valor: int,
        chavepix: str
    ):
        if valor <= 0:
            await interaction.response.send_message(
                "❌ Valor inválido.",
                ephemeral=True
            )
            return

        await ensure_user(interaction.user.id, interaction.user.name)

        async with pool.acquire() as conn:
            saldo = await conn.fetchval(
                "SELECT moedas FROM users WHERE user_id = $1",
                interaction.user.id
            )

        if saldo < valor:
            await interaction.response.send_message(
                "❌ Você não tem moedas suficientes.",
                ephemeral=True
            )
            return

        valor_reais = valor * 0.10

        guild = interaction.guild
        categoria = discord.utils.get(guild.categories, name="SAQUES")
        if not categoria:
            categoria = await guild.create_category("SAQUES")

        canal = await guild.create_text_channel(
            name=f"saque-{interaction.user.name}",
            category=categoria,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(ADM_ID): discord.PermissionOverwrite(read_messages=True),
            }
        )

        async with pool.acquire() as conn:
            saque_id = await conn.fetchval("""
                INSERT INTO saques (user_id, moedas, chave_pix, status)
                VALUES ($1, $2, $3, 'pendente')
                RETURNING id
            """, interaction.user.id, valor, chavepix)

        embed = discord.Embed(
            title="💸 SOLICITAÇÃO DE SAQUE",
            description=(
                f"🆔 **ID do Saque:** `{saque_id}`\n\n"
                f"👤 **Usuário:** {interaction.user.mention}\n"
                f"🔑 **Chave Pix:** `{chavepix}`\n\n"
                f"💰 **Moedas:** {valor}\n"
                f"💵 **Valor:** R$ {valor_reais:.2f}\n\n"
                "⚠️ Após o pagamento, o ADM deve usar:\n"
                "`/confirmarsaque id`"
            ),
            color=discord.Color.gold()
        )

        await canal.send(embed=embed)
        await interaction.response.send_message(
            f"📂 Saque criado em {canal.mention}",
            ephemeral=True
        )

    # ===============================
    # /confirmarsaque (ADM)
    # ===============================
    @app_commands.command(
        name="confirmarsaque",
        description="(ADM) Confirmar saque pago"
    )
    async def confirmar_saque(
        self,
        interaction: discord.Interaction,
        id: int
    ):
        if interaction.user.id != ADM_ID:
            await interaction.response.send_message(
                "❌ Apenas o ADM pode confirmar saques.",
                ephemeral=True
            )
            return

        async with pool.acquire() as conn:
            saque = await conn.fetchrow(
                "SELECT * FROM saques WHERE id = $1 AND status = 'pendente'",
                id
            )

        if not saque:
            await interaction.response.send_message(
                "❌ Saque não encontrado ou já confirmado.",
                ephemeral=True
            )
            return

        await remove_coins(saque["user_id"], saque["moedas"])

        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE saques
                SET status = 'confirmado'
                WHERE id = $1
            """, id)

        await interaction.channel.send(
            "✅ Saque confirmado! Canal será fechado em 10 segundos."
        )

        hist = self.bot.get_channel(CANAL_HISTORICO_SAQUE)
        if hist:
            await hist.send(
                f"💸 **SAQUE CONFIRMADO**\n"
                f"Usuário: <@{saque['user_id']}>\n"
                f"Moedas: {saque['moedas']}\n"
                f"Pix: `{saque['chave_pix']}`"
            )

        await asyncio.sleep(10)
        await interaction.channel.delete()


async def setup(bot):
    await bot.add_cog(Saque(bot))
