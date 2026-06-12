# backend/schemas.py
from pydantic import BaseModel
from typing import Dict, Any

class UserAuth(BaseModel):
    username: str
    password: str
    ecdh_key: Dict[str, Any]
    ecdsa_key: Dict[str, Any]

class ContactAdd(BaseModel):
    owner_username: str
    contact_username: str