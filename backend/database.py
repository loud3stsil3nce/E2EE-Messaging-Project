import os
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

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    # This explicit pool_pre_ping helps maintain connections in cloud environments
    pool_pre_ping=True 
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session