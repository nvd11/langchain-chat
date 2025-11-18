from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.configs.db import get_db_session
from src.schemas.user import UserSchema, UserCreateSchema
from src.dao import user_dao

router = APIRouter(
    prefix="/api/v1",
    tags=["Users & Conversations"],
)

@router.post("/users/", response_model=UserSchema)
async def create_user_endpoint(
    user: UserCreateSchema, db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new user.
    """
    db_user = await user_dao.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    created_user = await user_dao.create_user(db=db, user=user)
    return created_user

@router.get("/users/{username}", response_model=UserSchema)
async def get_user_endpoint(username: str, db: AsyncSession = Depends(get_db_session)):
    """
    Get a single user by username.
    """
    db_user = await user_dao.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
