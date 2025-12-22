import discord
from discord.ext import commands
import os
import asyncio
import threading

from flask import Flask
from database import init_db


# ===============================
# CONFIGURAÇÕES
# ===============================

TOKEN = os.getenv("DISCORD_TOKEN")

# ID DO SEU SERVIDOR (GUILD)
GUILD_ID = 1447592173913509919


# ===============================
# SERVIDOR HTTP (RENDER WEB)
# ===============================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot online"


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# ===============================
# BOT DISCORD
# ===============================

INTENTS = discord.Intents.default()
INTENTS.members = True


class BotEconomia(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=INTENTS
        )

    async def setup_hook(self):
        # Inicializa banco de dados
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
                print(f"❌ Erro ao carregar {ext}: {e}")

        # ===============================
        # SYNC APENAS NO SERVIDOR (IMEDIATO)
        # ===============================
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        print("🌐 Comandos sincronizados no servidor")


async def start_bot():
    bot = BotEconomia()
    await bot.start(TOKEN)


# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(start_bot())
