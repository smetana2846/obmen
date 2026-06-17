from app.database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    exchanges = relationship("Exchange", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String, index=True)
    network = Column(String, nullable=True)

    user = relationship("User", back_populates="favorites")

class Exchange(Base):
    __tablename__ = "exchanges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    from_currency = Column(String)
    to_currency = Column(String)
    from_network = Column(String, nullable=True)
    to_network = Column(String, nullable=True)
    amount_send = Column(Float)
    amount_receive_before_commission = Column(Float, default=0.0)
    amount_receive = Column(Float)
    commission_percent = Column(Float, default=1.5)
    commission_amount = Column(Float, default=0.0)
    deposit_address = Column(String)
    exchange_id = Column(String)
    status = Column(String, default="waiting")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="exchanges")