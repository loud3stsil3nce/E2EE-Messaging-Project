# backend/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.mysql import LONGTEXT
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    username = Column(String(255), primary_key=True, index=True)
    hashed_password = Column(String(255), nullable=False) # <-- NEW COLUMN
    
    ecdh_public_key = Column(Text, nullable=False)
    ecdsa_public_key = Column(Text, nullable=False)

    messages_received = relationship("Message", back_populates="recipient", foreign_keys='Message.recipient_username')

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_username = Column(String(255), nullable=False)
    recipient_username = Column(String(255), ForeignKey("users.username"), nullable=False)
    
    ciphertext = Column(LONGTEXT, nullable=False) 
    iv = Column(Text, nullable=False)         
    signature = Column(Text, nullable=False)  
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    recipient = relationship("User", back_populates="messages_received", foreign_keys=[recipient_username])
    
    
class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    # The person who owns the address book
    owner_username = Column(String(255), ForeignKey("users.username"), nullable=False, index=True)
    # The person they added
    contact_username = Column(String(255), ForeignKey("users.username"), nullable=False)