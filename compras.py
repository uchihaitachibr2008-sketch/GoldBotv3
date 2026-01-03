import discord
from discord import app_commands
from discord.ext import commands, tasks
import mercadopago
import asyncio
import os

from economia import add_coins
from database import pool, ensure_user

# ===============================
# CONFIGURAÇÕES
# ===============================

GUILD_ID = 1447592173913509919
ADM_ID = 969976402571063397
HISTORICO_COMPRAS = 1451350213146181703

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))


class Compras(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.verificar_pagamentos.start()

    # ===============================
    # SLASH COMMAND
    # ===============================

    @app_commands.command(
        name="comprar",
        description="Comprar moedas via Pix (1 moeda = R$ 0,10)"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def comprar(
        self,
        interaction: discord.Interaction,
        valor: float
    ):
        if valor <= 0:
            await interaction.response.send_message(
                "❌ Valor inválido.",
                ephemeral=True
            )
            return

        moedas = int(valor * 10)
        await ensure_user(interaction.user.id, interaction.user.name)

        guild = interaction.guild

        # ===============================
        # CRIA CATEGORIA / CANAL
        # ===============================

        categoria = discord.utils.get(guild.categories, name="COMPRAS")
        if not categoria:
            categoria = await guild.create_category("COMPRAS")

        canal = await guild.create_text_channel(
            name=f"compra-{interaction.user.name}".lower(),
            category=categoria,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(ADM_ID): discord.PermissionOverwrite(read_messages=True),
            }
        )

        # ===============================
        # CRIA PAGAMENTO PIX
        # ===============================

        payment = sdk.payment().create({
            "transaction_amount": float(valor),
            "description": f"Compra de {moedas} moedas",
            "payment_method_id": "pix",
            "payer": {
                "email": "comprador@discord.com"
            }
        })

        payment_id = payment["response"]["id"]
        qr_base64 = payment["response"]["point_of_interaction"]["transaction_data"]["qr_code_base64"]

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO compras (user_id, payment_id, valor, moedas, status)
                VALUES ($1, $2, $3, $4, 'pendente')
                """,
                interaction.user.id,
                payment_id,
                valor,
                moedas
            )

        embed = discord.Embed(
            title="💰 COMPRA DE MOEDAS",
            description=(
                f"Valor: **R$ {valor:.2f}**\n"
                f"Você receberá: **{moedas} moedas**\n\n"
                "📲 **Escaneie o QR Code abaixo para pagar via Pix.**\n"
                "As moedas serão entregues automaticamente após a confirmação."
            ),
            color=discord.Color.green()
        )

        embed.set_image(url=f"data:image/png;base64,{qr_base64}")

        await canal.send(content=interaction.user.mention, embed=embed)

        await interaction.response.send_message(
            f"🛒 Compra criada em {canal.mention}",
            ephemeral=True
        )

    # ===============================
    # VERIFICA PAGAMENTOS
    # ===============================

    @tasks.loop(seconds=30)
    async def verificar_pagamentos(self):
        async with pool.acquire() as conn:
            compras = await conn.fetch(
                "SELECT * FROM compras WHERE status = 'pendente'"
            )

        for compra in compras:
            payment = sdk.payment().get(compra["payment_id"])
            status = payment["response"]["status"]

            if status != "approved":
                continue

            await add_coins(compra["user_id"], compra["moedas"])

            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE compras
                    SET status = 'aprovado'
                    WHERE payment_id = $1
                    """,
                    compra["payment_id"]
                )

            guild = self.bot.get_guild(GUILD_ID)
            user = guild.get_member(compra["user_id"])

            canal = discord.utils.get(
                guild.text_channels,
                name=f"compra-{user.name}".lower() if user else None
            )

            if canal:
                await canal.send("✅ **Pagamento confirmado! Moedas entregues.**")
                await asyncio.sleep(5)
                await canal.delete()

            historico = self.bot.get_channel(HISTORICO_COMPRAS)
            if historico:
                await historico.send(
                    f"🟢 **Compra confirmada**\n"
                    f"Usuário: <@{compra['user_id']}>\n"
                    f"Moedas: {compra['moedas']}"
                )

    @verificar_pagamentos.before_loop
    async def before_verificar(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Compras(bot))
