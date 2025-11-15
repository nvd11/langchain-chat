import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from loguru import logger

from src.configs.config import yaml_configs

def build_db_url(db_config: dict) -> str | None:
    """Builds the database URL from configuration."""
    user_env_var = db_config.get("user_env_var")
    password_env_var = db_config.get("password_env_var")

    user = os.getenv(user_env_var)
    password = os.getenv(password_env_var)

    if not all([user, password]):
        logger.error(f"DB credentials not in env vars ('{user_env_var}', '{password_env_var}').")
        return None

    host = db_config.get("host")
    port = db_config.get("port")
    dbname = db_config.get("dbname")

    if not all([host, port, dbname]):
        logger.error("DB host, port, or dbname missing in config.")
        return None

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"

# --- Database Engine and Session Setup ---

# Default to a dummy URL to prevent crashes on import if config is missing.
DATABASE_URL = "postgresql+asyncpg://dummy:dummy@localhost/dummy"
db_config = yaml_configs.get("database") if yaml_configs else None

if db_config:
    url = build_db_url(db_config)
    if url:
        DATABASE_URL = url
        logger.info("Database connection URL built successfully.")
    else:
        logger.error("Failed to build database URL. Using dummy URL.")
else:
    logger.warning("Database configuration not found, using dummy URL.")

# Create an async engine.
async_engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,  # Set to True to see generated SQL statements
)

# Create a sessionmaker for creating AsyncSession instances
AsyncSessionFactory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for declarative models
Base = declarative_base()

async def get_db_session() -> AsyncSession:
    """Dependency to get a database session."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()

logger.info("Database engine and session factory configured.")
