"""创建用户表和相关表。

运行: uv run python scripts/create_user_tables.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg


async def main():
    # 连接 PostgreSQL
    print("连接 PostgreSQL...")
    conn = await asyncpg.connect(
        host="118.25.107.222",
        port=5432,
        user="postgres",
        password="Kp7sQv2#zRg9mBn&tA5",
        database="aiagent",
    )

    try:
        print("连接成功！")

        # 创建用户表
        print("\n创建 users 表...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ users 表创建成功")

        # 创建会话表
        print("\n创建 chat_sessions 表...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ chat_sessions 表创建成功")

        # 创建消息表
        print("\n创建 chat_messages 表...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ chat_messages 表创建成功")

        # 创建索引
        print("\n创建索引...")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id)")
        print("✓ 索引创建成功")

        # 验证表
        print("\n验证表结构...")
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name IN ('users', 'chat_sessions', 'chat_messages')
        """)
        print(f"已创建的表: {[t['table_name'] for t in tables]}")

        print("\n✅ 所有表创建完成！")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
