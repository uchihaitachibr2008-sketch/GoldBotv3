import discord
from discord.ext import commands
from discord import app_commands
import asyncio

ADM_ID = 969976402571063397


# ===============================
# VIEW DO BOTÃO (PERSISTENTE)
# ===============================

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Fechar Ticket",
        style=discord.ButtonStyle.red,
        custom_id="fechar_ticket"
    )
    async def fechar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        # Apenas ADM ou dono do ticket pode fechar
        if (
            interaction.user.id != ADM_ID
            and interaction.user != interaction.channel.topic
        ):
            await interaction.response.send_message(
                "❌ Você não pode fechar este ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "⏳ Ticket será fechado em 10 segundos..."
        )

        await asyncio.sleep(10)
        await interaction.channel.delete()


# ===============================
# COG DE TICKET
# ===============================

class Ticket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="ticket",
        description="Abrir um ticket de suporte"
    )
    @app_commands.describe(
        motivo="Explique o motivo do ticket"
    )
    async def ticket(
        self,
        interaction: discord.Interaction,
        motivo: str
    ):
        guild = interaction.guild

        # 🔒 BLOQUEIA TICKET DUPLICADO POR USUÁRIO
        for channel in guild.text_channels:
            if channel.name == f"ticket-{interaction.user.id}":
                await interaction.response.send_message(
                    f"❌ Você já tem um ticket aberto: {channel.mention}",
                    ephemeral=True
                )
                return

        # Categoria
        categoria = discord.utils.get(guild.categories, name="TICKETS")
        if not categoria:
            categoria = await guild.create_category("TICKETS")

        # Canal
        canal = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=categoria,
            topic=str(interaction.user.id),
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(ADM_ID): discord.PermissionOverwrite(read_messages=True),
            }
        )

        embed = discord.Embed(
            title="🎟️ TICKET ABERTO",
            description=(
                f"👤 **Usuário:** {interaction.user.mention}\n"
                f"📝 **Motivo:** {motivo}\n\n"
                "🔔 Um administrador irá te atender.\n"
                "Quando terminar, clique no botão abaixo para fechar."
            ),
            color=discord.Color.blue()
        )

        await canal.send(embed=embed, view=TicketView())

        await interaction.response.send_message(
            f"📂 Ticket criado em {canal.mention}",
            ephemeral=True
        )


# ===============================
# SETUP (NÃO DUPLICA)
# ===============================

async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot))
