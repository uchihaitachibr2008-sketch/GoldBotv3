import discord
from discord.ext import commands
import os
import asyncio
import threading

from flask import Flask
from database import init_db

GUILD_ID = 1447592173913509919

# ===============================
# SERVIDOR WEB (RENDER)
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

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True


class GoldBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        await init_db()

        # ❗ LIMPA COMANDOS GLOBAIS (ISS0 É O PULO DO GATO)
        self.tree.clear_commands(guild=None)

        extensoes = [
            "economia",
            "ticket"
        ]

        for ext in extensoes:
            try:
                await self.load_extension(ext)
                print(f"✅ {ext} carregado")
            except Exception as e:
                print(f"❌ Erro ao carregar {ext}: {e}")

        # 🔥 SINCRONIZA APENAS NO SEU SERVIDOR
        guild = discord.Object(id=GUILD_ID)
        await self.tree.sync(guild=guild)

        print("🌐 Comandos sincronizados no servidor")


async def start_bot():
    bot = GoldBot()
    await bot.start(TOKEN)


# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(start_bot())
