import discord
from discord.ext import commands
from discord import app_commands
import asyncio

GUILD_ID = 1447592173913509919
ADM_ID = 969976402571063397


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.closed = False  # 🔒 trava

    @discord.ui.button(
        label="🔒 Fechar Ticket",
        style=discord.ButtonStyle.red
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.closed:
            return

        self.closed = True
        await interaction.response.send_message(
            "⏳ Ticket será fechado em 10 segundos...",
            ephemeral=True
        )
        await asyncio.sleep(10)
        await interaction.channel.delete()


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ticket",
        description="Abrir um ticket de suporte"
    )
    async def ticket(self, interaction: discord.Interaction, motivo: str):
        guild = interaction.guild

        # 🔒 BLOQUEIA DUPLA EXECUÇÃO
        await interaction.response.defer(ephemeral=True)

        categoria = discord.utils.get(guild.categories, name="TICKETS")
        if not categoria:
            categoria = await guild.create_category("TICKETS")

        canal = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=categoria,
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
                "Use o botão abaixo para fechar o ticket."
            ),
            color=discord.Color.blue()
        )

        await canal.send(embed=embed, view=TicketView())

        await interaction.followup.send(
            f"📂 Ticket criado em {canal.mention}",
            ephemeral=True
        )


async def setup(bot):
    # 🚫 GARANTE QUE NÃO REGISTRA DUAS VEZES
    if "Ticket" not in bot.cogs:
        await bot.add_cog(Ticket(bot))
