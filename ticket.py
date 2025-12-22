from discord.ext import commands
from discord import app_commands
import discord

GUILD_ID = 1447592173913509919

ADM_ID = 969976402571063397


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Fechar Ticket",
        style=discord.ButtonStyle.red
    )
    async def fechar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "⏳ Ticket será fechado em 10 segundos..."
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
    async def ticket(
        self,
        interaction: discord.Interaction,
        motivo: str
    ):
        guild = interaction.guild

        categoria = discord.utils.get(guild.categories, name="TICKETS")
        if not categoria:
            categoria = await guild.create_category("TICKETS")

        canal = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
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
                "Quando o atendimento terminar, clique no botão abaixo para fechar."
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

