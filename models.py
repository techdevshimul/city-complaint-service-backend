from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default='user', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, default='')
    is_active = Column(Boolean, default=True, nullable=False)


class Complaint(Base):
    __tablename__ = 'complaints'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=False)
    location = Column(String(250), nullable=False)
    image_url = Column(String, nullable=True)
    priority = Column(String, default='medium', nullable=False, index=True)
    status = Column(String, default='pending', nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False, index=True)
    assigned_to_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StatusHistory(Base):
    __tablename__ = 'status_history'
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey('complaints.id'), nullable=False)
    status = Column(String, nullable=False)
    note = Column(String, default='')
    changed_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
