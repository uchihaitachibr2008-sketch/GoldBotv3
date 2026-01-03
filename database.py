import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")

pool = None


async def init_db():
    global pool

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não configurado")

    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=5,
        ssl="require"
    )

    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            moedas INTEGER DEFAULT 0,
            vitorias INTEGER DEFAULT 0,
            derrotas INTEGER DEFAULT 0,
            streak_atual INTEGER DEFAULT 0,
            streak_max INTEGER DEFAULT 0
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS x1 (
            id SERIAL PRIMARY KEY,
            jogador1 BIGINT,
            jogador2 BIGINT,
            valor INTEGER,
            status TEXT
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS missoes (
            user_id BIGINT,
            missao TEXT,
            concluida BOOLEAN DEFAULT FALSE,
            data DATE
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            valor_reais NUMERIC,
            moedas INTEGER,
            status TEXT
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS saques (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            moedas INTEGER,
            chave_pix TEXT,
            status TEXT
        );
        """)

    print("✅ Banco de dados inicializado com sucesso")


async def get_pool():
    if not pool:
        raise RuntimeError("Banco de dados não inicializado")
    return pool

