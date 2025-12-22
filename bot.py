import discord
from discord.ext import commands
import os
import asyncio

from database import init_db

GUILD_ID = 1447592173913509919
TOKEN = os.getenv("DISCORD_TOKEN")

INTENTS = discord.Intents.default()
INTENTS.members = True


class BotEconomia(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=INTENTS
        )

    async def setup_hook(self):
        await init_db()

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
                print(f"❌ ERRO em {ext}: {e}")

        guild = discord.Object(id=GUILD_ID)

        # 🔥 sincroniza TUDO no servidor
        synced = await self.tree.sync(guild=guild)
        print(f"🌐 {len(synced)} comandos sincronizados")

    async def on_ready(self):
        print(f"🤖 Bot conectado como {self.user}")


async def main():
    bot = BotEconomia()
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
