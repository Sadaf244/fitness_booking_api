from sqlalchemy import Column, Integer, String, DateTime, Boolean, CheckConstraint,UniqueConstraint
from sqlalchemy.orm import validates
from database import Base
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from pytz import utc
from sqlalchemy import func
import re

class FitnessClass(Base):
    __tablename__ = 'classes'
    __table_args__ = (
        CheckConstraint('end_time > start_time', name='check_class_times'),
        CheckConstraint('available_slots >= 0', name='check_available_slots'),
        CheckConstraint('capacity > 0', name='check_capacity')
    )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    instructor = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False)
    available_slots = Column(Integer, nullable=False)
    timezone = Column(String(50), default='UTC')
    bookings = relationship("Booking", back_populates="fitness_class")
    status = Column(String(20), default='upcoming') # 'upcoming', 'completed', 'cancelled'
    is_active = Column(Boolean, default=True)

    @validates('start_time', 'end_time')
    def validate_times(self, key, time):
        if time.tzinfo is None:
            raise ValueError("Time must be timezone-aware") 
        return time.astimezone(utc)
        
    @validates('name')
    def validate_name(self, key, name):
        if len(name) < 2 or len(name) > 50:
            raise ValueError("Name must be between 2 and 50 characters")
        return name
    
    @validates('available_slots')
    def validate_slots(self, key, slots):
        if slots < 0:
            raise ValueError("Available slots cannot be negative")
        if hasattr(self, 'capacity') and slots > self.capacity:
            raise ValueError("Available slots cannot exceed capacity")
        return slots

class Booking(Base):
    __tablename__ = 'bookings'
    __table_args__ = (
        UniqueConstraint('class_id', 'client_email', name='unique_booking'),
    )
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(50), nullable=False)
    client_email = Column(String(255), nullable=False)
    booking_time = Column(DateTime, default=datetime.utcnow)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    fitness_class = relationship("FitnessClass", back_populates="bookings")
    checked_in = Column(Boolean, default=False)
    is_cancelled = Column(Boolean, default=False)

    @validates('client_email')
    def validate_email(self, key, email):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email): 
            raise ValueError("Invalid email format")
        return email.lower()