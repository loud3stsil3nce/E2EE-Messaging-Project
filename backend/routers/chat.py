# backend/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
import json

from database import get_db
from models import User, Message, Contact
from schemas import ContactAdd

router = APIRouter(tags=["Chat & Contacts"])

@router.get("/users/{username}/keys")
async def get_user_keys(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "ecdh_key": json.loads(user.ecdh_public_key),
        "ecdsa_key": json.loads(user.ecdsa_public_key)
    }
    
@router.get("/messages/{user1}/{user2}")
async def get_chat_history(user1: str, user2: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message)
        .where(
            or_(
                and_(Message.sender_username == user1, Message.recipient_username == user2),
                and_(Message.sender_username == user2, Message.recipient_username == user1)
            )
        )
        .order_by(Message.timestamp.asc())
    )
    return [
        {
            "from": msg.sender_username,
            "iv": json.loads(msg.iv),
            "ciphertext": json.loads(msg.ciphertext),
            "signature": json.loads(msg.signature),
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in result.scalars().all()
    ]

@router.post("/contacts/add")
async def add_contact(data: ContactAdd, db: AsyncSession = Depends(get_db)):
    owner, contact = data.owner_username, data.contact_username
    if owner == contact: raise HTTPException(status_code=400, detail="Cannot add yourself.")

    if not (await db.execute(select(User).where(User.username == contact))).scalars().first():
        raise HTTPException(status_code=404, detail="User does not exist.")

    if (await db.execute(select(Contact).where(and_(Contact.owner_username == owner, Contact.contact_username == contact)))).scalars().first():
        raise HTTPException(status_code=400, detail="User already in contacts.")

    db.add(Contact(owner_username=owner, contact_username=contact))
    await db.commit()
    return {"status": "success", "message": f"Added {contact} to contacts."}

@router.get("/contacts/{username}")
async def get_contacts(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.owner_username == username))
    return [c.contact_username for c in result.scalars().all()]

@router.get("/inbox/{username}")
async def get_inbox(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message)
        .where(or_(Message.sender_username == username, Message.recipient_username == username))
        .order_by(Message.timestamp.desc()) 
    )
    
    recent_chats, seen_users = [], set()
    for msg in result.scalars().all():
        peer = msg.recipient_username if msg.sender_username == username else msg.sender_username
        if peer not in seen_users:
            seen_users.add(peer)
            recent_chats.append({"username": peer, "last_message_time": msg.timestamp.isoformat()})
    return recent_chats