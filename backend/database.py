import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")


connect_args = {
    "ssl": {"ssl_ca": None} 
}


clean_url = DATABASE_URL.split("?")[0]

engine = create_async_engine(
    clean_url, 
    connect_args=connect_args,
    echo=True # Set to False in production, True helps us debug right now
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session