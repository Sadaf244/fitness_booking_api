from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from fastapi_cache.decorator import cache
from schemas import BookingCreate, BookingResponse
from services.booking_service import BookingService
from services.class_service import ClassService
from database import get_db
import logging
from utils.errors import raise_404_if_none
from models import Booking, FitnessClass
from datetime import datetime, timedelta
from pytz import utc
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(booking: BookingCreate, db: Session = Depends(get_db)) -> BookingResponse:
    try:
        with db.begin_nested():  # Start atomic transaction
            # Validate booking data
            BookingService.validate_booking(db, booking)
            # 1. Verify class exists
            fitness_class = ClassService.get_class(db, booking.class_id)
            raise_404_if_none(fitness_class, "Fitness class")

            # 2. Lock and check class (WITHOUT committing)
            locked_class = (
                db.query(FitnessClass)
                .filter(FitnessClass.id == booking.class_id)
                .with_for_update()
                .first()
            )
            
            if not locked_class or locked_class.available_slots <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No available slots"
                )

            # 3. Decrement slots (not committed yet)
            locked_class.available_slots -= 1

            # 4. Create booking
            new_booking = Booking(**booking.dict())
            db.add(new_booking)
            
            # Both operations will commit together or roll back together
            db.commit()  # Explicit commit for the nested transaction

            logger.info(f"Booking created for {booking.client_email}")
            return new_booking

    except HTTPException:
        raise  # Re-raise validation errors
        
    except Exception as e:
        db.rollback()
        logger.error(f"Booking failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete booking"
        )


@router.get("/", response_model=List[BookingResponse])
def get_bookings(email: str, db: Session = Depends(get_db)):
    return BookingService.get_bookings_by_email(db, email)
# @router.get("/")
# def debug_bookings(email: str, db: Session = Depends(get_db)):
#     bookings = db.query(Booking).filter_by(client_email=email).all()
#     return {"count": len(bookings), "raw_data": bookings}