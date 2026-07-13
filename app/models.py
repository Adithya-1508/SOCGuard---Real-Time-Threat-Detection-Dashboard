# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, func, Float, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    severity = Column(Float, nullable=False)
    source = Column(String)        # e.g., "auth_log", "api_gate"
    summary = Column(String)
    details = Column(Text)
    ip = Column(String)
    status = Column(String, default="new")
    reputation_score = Column(Integer, nullable=True)
    threat_tags = Column(String, nullable=True) # JSON string of tags
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    explanation = Column(Text, nullable=True)
    agent_report = Column(Text, nullable=True)
    
    assignee = relationship("User", backref="alerts")
    comments = relationship("Comment", back_populates="alert", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    full_name = Column(String, nullable=True)
    role = Column(String, default="analyst") # admin, analyst, readonly, api

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    alert = relationship("Alert", back_populates="comments")
    user = relationship("User")

class SystemSettings(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String) # Store as JSON string if needed

class Playbook(Base):
    __tablename__ = "playbooks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    steps = Column(Text, nullable=False) # JSON or text steps
    embedding = Column(Text, nullable=True) # JSON string of floats
