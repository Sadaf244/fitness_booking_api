from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import FitnessClass
from schemas import FitnessClassResponse
from services.class_service import ClassService
from database import get_db
from services.slot_management_service import SlotManagementService

router = APIRouter(prefix="/classes", tags=["classes"])

@router.get("/", response_model=List[FitnessClassResponse])
def get_all_classes(db: Session = Depends(get_db), timezone: str = None):
    return ClassService.get_all_classes(db, timezone)
  
@router.post("/{class_id}/cancel", status_code=200)
def cancel_class(
    class_id: int,
    db: Session = Depends(get_db)
):
    """Admin endpoint to cancel a class"""
    SlotManagementService.cancel_class(db, class_id)
    return {"message": "Class cancelled successfully"}

@router.post("/{class_id}/check-in/{booking_id}", status_code=200)
def check_in_attendee(
    class_id: int,
    booking_id: int,
    db: Session = Depends(get_db)
):
    """Mark an attendee as present"""
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.class_id == class_id,
        Booking.is_cancelled == False
    ).first()
    
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    
    booking.checked_in = True
    db.commit()
    return {"message": "Attendee checked in successfully"}
