from sqlalchemy import Column,Integer,String,ForeignKey,DateTime
from database import engine
from sqlalchemy.orm import declarative_base,relationship
from datetime import datetime

Base=declarative_base()

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    username=Column(String,unique=True,nullable=False)
    password_hash=Column(String,nullable=False)
    role=Column(String,nullable=False)
    balance=Column(Integer,nullable=False,default=0)
    sessions=relationship("GameSession",back_populates="user")
    deposits=relationship("Deposit",back_populates="user")

class GameSession(Base):
    __tablename__="sessions"

    id=Column(String,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    user=relationship("User",back_populates="sessions")
    bets=relationship("Bet",back_populates="session")

class Bet(Base):
    __tablename__="bets"

    id=Column(Integer,primary_key=True)
    session_id=Column(String,ForeignKey("sessions.id"),nullable=False)
    bet_amount=Column(Integer,nullable=False)
    lines=Column(Integer,nullable=False)
    winnings=Column(Integer,nullable=False)
    net_result=Column(Integer,nullable=False)  
    created_at=Column(DateTime,default=datetime.utcnow,nullable=False)  
    session=relationship("GameSession",back_populates="bets")

class Deposit(Base):
    __tablename__="deposits"

    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    amount=Column(Integer,nullable=False)
    created_at=Column(DateTime,default=datetime.utcnow,nullable=False)
    user=relationship("User",back_populates="deposits")

Base.metadata.create_all(engine)