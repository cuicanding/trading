"""
数据库初始化脚本
创建users表和password_reset_tokens表
"""
import duckdb
import uuid


def init_database(db_path: str = "trading.db"):
    """初始化数据库，创建必要的表和索引"""
    
    # 连接到DuckDB数据库
    conn = duckdb.connect(db_path)
    
    # 创建users表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建password_reset_tokens表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id),
            token VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token)")
    
    # 关闭连接
    conn.close()
    
    print(f"数据库初始化完成: {db_path}")


if __name__ == "__main__":
    init_database()
