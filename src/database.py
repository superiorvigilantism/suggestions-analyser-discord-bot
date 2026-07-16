from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from models import Base, ServerData

# Import database URL from fetch_creds.py
from fetch_creds import DATABASE_URL


engine = create_async_engine(
    DATABASE_URL,
    # Debug mode off
    echo=False,
    # 10 perma-open connections
    pool_size=10,
    # 20 maximum connections (Should add)
    max_overflow=20,
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Creates all tables in the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close the database connection."""
    await engine.dispose()

async def get_server_data(guild_id: int) -> ServerData:
    """Retrieve the ServerData row for a guild"""
    async with async_session() as session:
        result = await session.execute(
            select(ServerData).where(ServerData.guild_id == guild_id)
        )
        # .scalars() gets just the object (not wrapped in a row)
        # .first() gets the first (and only) result, or None if no match
        return result.scalars().first()

async def update_server_data(guild_id: int, threshold: int = None, prompt: str = None, 
							 forward_channel_id: int = None, forum_channel_id: int = None):
    """Create or update ServerData for a guild"""
    async with async_session() as session:
        data = await session.get(ServerData, guild_id)
        
        if data:
            if threshold is not None:
                data.threshold = threshold
            if prompt is not None:
                data.prompt = prompt
            if forward_channel_id is not None:
            	data.forward_channel_id = forward_channel_id
            if forum_channel_id is not None:
            	data.forum_channel_id = forum_channel_id
        else:
            data = ServerData(
                guild_id=guild_id, 
                threshold=threshold or 6.0, 
                prompt=prompt or "You are a game suggestions evaluator. "
                                 "Rate every suggestion you are presented with by following format:"
                                 "\nScore: X/10"
                                 "\nReasoning: Lorem Ipsum dolor sit amet...", 
                forward_channel_id=-1,
                forum_channel_id=-1)
            
            session.add(data)
        
        await session.commit()
        return data

async def delete_server_data(guild_id: int):
    """Delete ServerData for a guild"""
    async with async_session() as session:
        data = await session.get(ServerData, guild_id)
        if data:
            await session.delete(data)
            await session.commit()
            return True
        return False
