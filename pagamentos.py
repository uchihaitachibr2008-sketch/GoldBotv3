import discord
from discord.ext import commands, tasks
from discord import app_commands
import mercadopago
import asyncio
import os

from database import pool, ensure_user
from economia import add_coins
from config import (
    ADM_ID,
    CANAL_COMPRAS_HISTORICO_ID,
    VALOR_MOEDA_REAIS
)

# ===============================
# MERCADO PAGO
# ===============================
MP_TOKEN = os.getenv("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(MP_TOKEN)


# ===============================
# COG PAGAMENTOS
# ===============================
class Pagamentos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verificar_pagamentos.start()

    # ===============================
    # /comprar
    # ===============================
    @app_commands.command(
        name="comprar",
        description="Comprar moedas via Pix"
    )
    async def comprar(self, interaction: discord.Interaction, valor_reais: float):
        if valor_reais <= 0:
            await interaction.response.send_message(
                "❌ Valor inválido.",
                ephemeral=True
            )
            return

        await ensure_user(interaction.user.id, interaction.user.name)

        moedas = int(valor_reais / VALOR_MOEDA_REAIS)

        if moedas <= 0:
            await interaction.response.send_message(
                "❌ Valor muito baixo.",
                ephemeral=True
            )
            return

        guild = interaction.guild

        categoria = discord.utils.get(guild.categories, name="COMPRAS")
        if not categoria:
            categoria = await guild.create_category("COMPRAS")

        canal = await guild.create_text_channel(
            name=f"compra-{interaction.user.name}".lower(),
            category=categoria,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True),
                guild.get_member(ADM_ID): discord.PermissionOverwrite(view_channel=True),
            }
        )

        # ===============================
        # CRIA PAGAMENTO PIX
        # ===============================
        pagamento = sdk.payment().create({
            "transaction_amount": float(valor_reais),
            "description": f"Compra de {moedas} moedas",
            "payment_method_id": "pix",
            "payer": {
                "email": f"{interaction.user.id}@discord.com"
            }
        })

        payment_id = pagamento["response"]["id"]
        qr_base64 = pagamento["response"]["point_of_interaction"]["transaction_data"]["qr_code_base64"]

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO compras (user_id, valor_reais, moedas, status)
                VALUES ($1, $2, $3, 'pendente')
            """, interaction.user.id, valor_reais, moedas)

        embed = discord.Embed(
            title="💰 COMPRA DE MOEDAS",
            description=(
                f"👤 Usuário: {interaction.user.mention}\n"
                f"💵 Valor: **R$ {valor_reais:.2f}**\n"
                f"🪙 Moedas: **{moedas}**\n\n"
                "📲 **Escaneie o QR Code para pagar via Pix**\n"
                "Assim que o pagamento for confirmado, as moedas serão entregues automaticamente."
            ),
            color=discord.Color.green()
        )

        embed.set_image(url=f"data:image/png;base64,{qr_base64}")

        await canal.send(embed=embed)

        await interaction.response.send_message(
            f"🛒 Compra criada em {canal.mention}",
            ephemeral=True
        )

    # ===============================
    # VERIFICAR PAGAMENTOS
    # ===============================
    @tasks.loop(seconds=30)
    async def verificar_pagamentos(self):
        async with pool.acquire() as conn:
            compras = await conn.fetch("""
                SELECT * FROM compras WHERE status = 'pendente'
            """)

        for compra in compras:
            pagamento = sdk.payment().get(compra["id"])
            status = pagamento["response"]["status"]

            if status == "approved":
                await add_coins(compra["user_id"], compra["moedas"])

                async with pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE compras
                        SET status = 'aprovado'
                        WHERE id = $1
                    """, compra["id"])

                guild = self.bot.guilds[0]
                user = self.bot.get_user(compra["user_id"])

                canal = discord.utils.get(
                    guild.text_channels,
                    name=f"compra-{user.name}".lower()
                )

                if canal:
                    await canal.send("✅ **Pagamento confirmado! Moedas entregues.**")
                    await asyncio.sleep(5)
                    await canal.delete()

                hist = self.bot.get_channel(CANAL_COMPRAS_HISTORICO_ID)
                if hist:
                    await hist.send(
                        f"🟢 **COMPRA CONFIRMADA**\n"
                        f"Usuário: <@{compra['user_id']}>\n"
                        f"Moedas: {compra['moedas']}\n"
                        f"Valor: R$ {compra['valor_reais']:.2f}"
                    )

    @verificar_pagamentos.before_loop
    async def before_verificar(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Pagamentos(bot))
