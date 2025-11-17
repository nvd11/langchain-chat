from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from typing import List

from src.models.tables import conversations_table
from src.schemas.conversation import ConversationCreateSchema

async def create_conversation(db: AsyncSession, conv: ConversationCreateSchema) -> dict:
    """
    Creates a new conversation for a user.
    """
    query = insert(conversations_table).values(
        user_id=conv.user_id
    ).returning(conversations_table)
    
    result = await db.execute(query)
    created_conv = result.first()
    await db.commit()
    return created_conv._asdict()

async def get_conversations_by_user(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10) -> List[dict]:
    """
    Fetches all conversations for a specific user.
    """
    query = select(conversations_table).where(
        conversations_table.c.user_id == user_id
    ).offset(skip).limit(limit)
    
    result = await db.execute(query)
    conversations = result.fetchall()
    return [conv._asdict() for conv in conversations]
