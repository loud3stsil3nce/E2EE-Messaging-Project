import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get the URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# FORCE the dialect to aiomysql if it's currently mysql://
# This prevents SQLAlchemy from looking for the 'MySQLdb' C-library
if DATABASE_URL and DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+aiomysql://")

# Intercept SSL configuration to prevent asyncio/aiomysql crashes
connect_args = {}
if DATABASE_URL and ("ssl=" in DATABASE_URL or "ssl_ca" in DATABASE_URL or "ssl-mode" in DATABASE_URL):
    # Strip problematic query parameters from the URL string
    for param in ["?ssl=true", "&ssl=true", "?ssl_ca=/etc/ssl/certs/ca-certificates.crt", "&ssl_ca=/etc/ssl/certs/ca-certificates.crt", "?ssl-mode=REQUIRED", "&ssl-mode=REQUIRED"]:
        DATABASE_URL = DATABASE_URL.replace(param, "")
        
    # Configure a valid SSLContext for Python asyncio/aiomysql
    ssl_context = ssl.create_default_context()
    connect_args["ssl"] = ssl_context

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    # This explicit pool_pre_ping helps maintain connections in cloud environments
    pool_pre_ping=True,
    connect_args=connect_args  # Pass the proper SSL Context here
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session
