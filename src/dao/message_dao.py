from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from typing import List

from src.models.tables import messages_table
from src.schemas.message import MessageCreateSchema

async def create_message(db: AsyncSession, message: MessageCreateSchema) -> dict:
    """
    Creates a new message in a conversation.
    """
    query = insert(messages_table).values(
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content
    ).returning(messages_table)
    
    result = await db.execute(query)
    created_message = result.first()
    await db.commit()
    return created_message._asdict()

async def get_messages_by_conversation(db: AsyncSession, conversation_id: int) -> List[dict]:
    """
    Fetches all messages for a specific conversation.
    """
    query = select(messages_table).where(
        messages_table.c.conversation_id == conversation_id
    ).order_by(messages_table.c.created_at)
    
    result = await db.execute(query)
    messages = result.fetchall()
    return [msg._asdict() for msg in messages]
