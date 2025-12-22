import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")
pool = None

# ===============================
# CONEXÃO COM O BANCO
# ===============================

async def connect_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    await create_tables()

# ===============================
# CRIAÇÃO DAS TABELAS
# ===============================

async def create_tables():
    async with pool.acquire() as conn:

        # USUÁRIOS
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            max_streak INTEGER DEFAULT 0
        );
        """)

        # CARTEIRA
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS wallet (
            user_id BIGINT PRIMARY KEY,
            coins INTEGER DEFAULT 0
        );
        """)

        # X1
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS x1_matches (
            id SERIAL PRIMARY KEY,
            challenger BIGINT,
            opponent BIGINT,
            value INTEGER,
            status TEXT,
            winner BIGINT,
            admin_fee INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # VOTOS X1
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS x1_votes (
            match_id INTEGER,
            voter_id BIGINT,
            voted_id BIGINT,
            PRIMARY KEY (match_id, voter_id)
        );
        """)

        # STREAK / CAÇA
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS streaks (
            user_id BIGINT PRIMARY KEY,
            multiplier FLOAT DEFAULT 1.0,
            hunt_reward INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT FALSE
        );
        """)

        # MISSÕES
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS missions (
            id SERIAL PRIMARY KEY,
            difficulty TEXT,
            description TEXT,
            reward INTEGER,
            bonus BOOLEAN DEFAULT FALSE
        );
        """)

        # MISSÕES DO USUÁRIO
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_missions (
            user_id BIGINT,
            mission_id INTEGER,
            completed BOOLEAN DEFAULT FALSE,
            date DATE,
            PRIMARY KEY (user_id, mission_id, date)
        );
        """)

        # COMPRAS
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            user_id BIGINT,
            value_reais FLOAT,
            coins INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # SAQUES
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS withdraws (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            coins INTEGER,
            value_reais FLOAT,
            pix_key TEXT,
            pix_name TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # TICKETS
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            reason TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # EVENTO DE CAÇA
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS hunt_events (
            user_id BIGINT PRIMARY KEY,
            reward INTEGER,
            losses INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT TRUE
        );
        """)

# ===============================
# FUNÇÕES BÁSICAS
# ===============================

async def ensure_user(user_id: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("""
        INSERT INTO users (user_id, username)
        VALUES ($1, $2)
        ON CONFLICT (user_id) DO NOTHING
        """, user_id, username)

        await conn.execute("""
        INSERT INTO wallet (user_id)
        VALUES ($1)
        ON CONFLICT (user_id) DO NOTHING
        """, user_id)

        await conn.execute("""
        INSERT INTO streaks (user_id)
        VALUES ($1)
        ON CONFLICT (user_id) DO NOTHING
        """, user_id)
