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
        custom_id="fechar_ticket"
    )
    async def fechar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        # Evita erro de interaction expirada
        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send(
            "⏳ Ticket será fechado em **10 segundos**...",
            ephemeral=True
        )

        await asyncio.sleep(10)

        try:
            await interaction.channel.delete()
        except Exception as e:
            print(f"Erro ao deletar ticket: {e}")


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ticket",
        description="Abrir um ticket de suporte"
    )
    @app_commands.describe(
        motivo="Descreva o motivo do ticket"
    )
    async def ticket(
        self,
        interaction: discord.Interaction,
        motivo: str
    ):
        guild = interaction.guild

        categoria = discord.utils.get(guild.categories, name="TICKETS")
        if not categoria:
            categoria = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
        }

        admin = guild.get_member(ADM_ID)
        if admin:
            overwrites[admin] = discord.PermissionOverwrite(read_messages=True)

        canal = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}".lower(),
            category=categoria,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎟️ TICKET ABERTO",
            description=(
                f"👤 **Usuário:** {interaction.user.mention}\n"
                f"📝 **Motivo:** {motivo}\n\n"
                "🔔 Um administrador irá te atender.\n"
                "Clique no botão abaixo para fechar o ticket."
            ),
            color=discord.Color.blue()
        )

        await canal.send(embed=embed, view=TicketView())

        await interaction.response.send_message(
            f"📂 Ticket criado em {canal.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Ticket(bot))
