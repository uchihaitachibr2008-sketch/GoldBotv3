import discord
from discord.ext import commands
from discord import app_commands
import asyncio

GUILD_ID = 1447592173913509919
ADM_ID = 969976402571063397


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Fechar Ticket",
        style=discord.ButtonStyle.red,
        custom_id="ticket_fechar"
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            "⏳ Ticket será fechado em **10 segundos**...",
            ephemeral=True
        )
        await asyncio.sleep(10)
        await interaction.channel.delete()


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(TicketView())  # ← REGISTRO PERSISTENTE

    @app_commands.command(name="ticket", description="Abrir um ticket de suporte")
    @app_commands.describe(motivo="Descreva o motivo do ticket")
    async def ticket(self, interaction: discord.Interaction, motivo: str):

        guild = interaction.guild

        # 🔒 VERIFICA SE JÁ EXISTE TICKET
        categoria = discord.utils.get(guild.categories, name="TICKETS")
        if categoria:
            for canal in categoria.text_channels:
                if canal.name == f"ticket-{interaction.user.id}":
                    await interaction.response.send_message(
                        f"❌ Você já possui um ticket aberto: {canal.mention}",
                        ephemeral=True
                    )
                    return

        if not categoria:
            categoria = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
        }

        admin = guild.get_member(ADM_ID)
        if admin:
            overwrites[admin] = discord.PermissionOverwrite(view_channel=True)

        canal = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=categoria,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎟️ TICKET ABERTO",
            description=(
                f"👤 **Usuário:** {interaction.user.mention}\n"
                f"📝 **Motivo:** {motivo}\n\n"
                "🔔 Um administrador irá te atender.\n"
                "Use o botão abaixo para fechar o ticket."
            ),
            color=discord.Color.blue()
        )

        await canal.send(embed=embed, view=TicketView())

        await interaction.response.send_message(
            f"✅ Ticket criado em {canal.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Ticket(bot))
