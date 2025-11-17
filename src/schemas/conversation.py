from pydantic import BaseModel
from datetime import datetime
from typing import List

from .message import MessageSchema

class ConversationBase(BaseModel):
    user_id: int

class ConversationCreateSchema(ConversationBase):
    pass

class ConversationSchema(ConversationBase):
    id: int
    created_at: datetime

class ConversationWithMessagesSchema(ConversationSchema):
    messages: List[MessageSchema] = []
