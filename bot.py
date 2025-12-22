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

GUILD_ID = 1447592173913509919
TOKEN = os.getenv("DISCORD_TOKEN")

INTENTS = discord.Intents.default()
INTENTS.members = True

# ===============================
# SERVIDOR HTTP (RENDER)
# ===============================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

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
        # Banco de dados
        await init_db()

        # 🔒 REMOVE QUALQUER COMANDO GLOBAL
        self.tree.clear_commands(guild=None)

        # 🔥 REGISTRO APENAS NO GUILD
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

        # 🔁 SINCRONIZA APENAS NO SERVIDOR
        await self.tree.sync(guild=guild)
        print("🌐 Comandos sincronizados apenas no servidor")

    async def on_ready(self):
        print(f"🤖 Bot conectado como {self.user}")

# ===============================
# START
# ===============================

async def start_bot():
    bot = BotEconomia()
    await bot.start(TOKEN)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(start_bot())
