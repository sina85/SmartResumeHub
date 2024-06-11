from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from psql import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class UserCredits(Base):
    __tablename__ = 'user_credits'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    credits = Column(Integer, default=0)
    user = relationship("User", back_populates="credits")

User.credits = relationship("UserCredits", back_populates="user")
