import discord
from discord.ext import commands
import os
import asyncio

from database import init_db

# ===============================
# CONFIGURAÇÕES
# ===============================

GUILD_ID = 1447592173913509919
TOKEN = os.getenv("DISCORD_TOKEN")

INTENTS = discord.Intents.default()
INTENTS.members = True

# ===============================
# BOT
# ===============================

class BotEconomia(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=INTENTS
        )

    async def setup_hook(self):
        await init_db()

        guild = discord.Object(id=GUILD_ID)

        extensoes = [
            "economia",
            "x1",
            "missoes",
            "compras",
            "saque",
            "cacar",
            "ticket",
            "rank_saldo"
        ]

        for ext in extensoes:
            try:
                await self.load_extension(ext)
                print(f"✅ {ext} carregado")
            except Exception as e:
                print(f"❌ Erro ao carregar {ext}: {e}")

        # 🔒 Sincroniza APENAS no servidor
        await self.tree.sync(guild=guild)
        print("🌐 Comandos sincronizados apenas no servidor")

    async def on_ready(self):
        print(f"🤖 Bot conectado como {self.user}")

# ===============================
# START
# ===============================

async def main():
    bot = BotEconomia()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
