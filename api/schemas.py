from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime
from typing import Optional
import re
from datetime import timedelta

class FitnessClassBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    instructor: str = Field(min_length=2, max_length=50)
    start_time: datetime
    end_time: datetime
    capacity: int = Field(gt=1, le=100)
    timezone: Optional[str] = 'Asia/Kolkata'
    
    @validator('end_time')
    def validate_times(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError("End time must be after start time")
        if 'start_time' in values and (v - values['start_time']) > timedelta(hours=3):
            raise ValueError("Class duration cannot exceed 3 hours")
        return v

    @validator('name')
    def validate_class_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\s\-]+$', v):
            raise ValueError("Class name can only contain letters, numbers, spaces and hyphens")
        return v.title()

class FitnessClassCreate(FitnessClassBase):
    pass

class FitnessClassResponse(FitnessClassBase):
    id: int
    available_slots: int
  
    class Config:
        orm_mode = True
        json_encoders = {   
            datetime: lambda v: v.isoformat()
        }   


class BookingBase(BaseModel):
    class_id: int = Field(gt=0)
    client_name: str = Field(min_length=2, max_length=50)
    client_email: EmailStr = Field(example="alice@example.com")

    class Config:
        anystr_strip_whitespace = True

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: int
    booking_time: datetime
    checked_in: bool
    is_cancelled: bool
    fitness_class: FitnessClassResponse  # This must match your joinedload
    
    class Config:
        orm_mode = True
    