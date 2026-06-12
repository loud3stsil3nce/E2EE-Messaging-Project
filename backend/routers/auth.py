# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import json

from database import get_db
from models import User
from schemas import UserAuth
from utils.crypto import get_password_hash, verify_password

router = APIRouter(tags=["Authentication"])

@router.post("/register")
async def register_user(user_data: UserAuth, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists.")
    
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        ecdh_public_key=json.dumps(user_data.ecdh_key),
        ecdsa_public_key=json.dumps(user_data.ecdsa_key)
    )
    db.add(new_user)
    await db.commit()
    return {"status": "success", "message": "User registered securely."}

@router.post("/login")
async def login_user(user_data: UserAuth, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    
    user.ecdh_public_key = json.dumps(user_data.ecdh_key)
    user.ecdsa_public_key = json.dumps(user_data.ecdsa_key)
    await db.commit()
    return {"status": "success", "message": "Login successful."}