from sqlalchemy.orm import Session, joinedload
from models import Booking,  FitnessClass
from schemas import BookingCreate, BookingResponse
from typing import List
import logging
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from pytz import utc
from sqlalchemy import func
logger = logging.getLogger(__name__)

class BookingService:
    @staticmethod
    def validate_booking(db: Session, booking_data: BookingCreate):
        # Get the class once and reuse it
        fitness_class = db.query(FitnessClass).filter(
            FitnessClass.id == booking_data.class_id
        ).first()
        
        if not fitness_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class with ID {booking_data.class_id} not found"
            )

        now = datetime.now(utc)  
        class_time = fitness_class.start_time
        if class_time.tzinfo is None:
            class_time = utc.localize(class_time)    
        # Check available slots
        if fitness_class.available_slots <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No available slots for this class"
            )
            
        # Check if class hasn't already happened
        if class_time  < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot book a class that has already started"
            )
            
        # Check if booking is too close to class time
        if (class_time - now) < timedelta(hours=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking must be made at least 1 hour before the class starts"
            )
            
        # Check if client already booked this class
        existing_booking = db.query(Booking).join(FitnessClass).filter(
            Booking.class_id == booking_data.class_id,
            Booking.client_email == booking_data.client_email
        ).first()

        if existing_booking:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already booked this class"
            )
            
        # Check booking limit
        upcoming_bookings = db.query(Booking).join(FitnessClass, Booking.class_id == FitnessClass.id).filter(
            Booking.client_email == booking_data.client_email,
            FitnessClass.start_time > now
        ).count()
        
        if upcoming_bookings >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot book more than 3 classes at a time"
            )

    @staticmethod
    def create_booking(db: Session, booking_data: BookingCreate) -> Booking:
        try:
            with db.begin_nested():  # Use a nested transaction
                BookingService.validate_booking(db, booking_data)
                
                # Get class with row lock
                fitness_class = db.query(FitnessClass).filter(
                    FitnessClass.id == booking_data.class_id,
                    FitnessClass.is_active == True
                ).with_for_update().first()

                # Check if class exists and is active
                if not fitness_class:
                    raise HTTPException(404, "Class not found or inactive")
        
                if fitness_class.status == 'cancelled' or fitness_class.status == 'completed':
                    raise HTTPException(400, "Cannot book completed or cancelled classes")
                # Create booking
                new_booking = Booking(**booking_data.dict())
                fitness_class.available_slots -= 1
                
                db.add(new_booking)
                db.commit()  # This commits the nested transaction
                
                logger.info(
                    f"Booking created - Class: {booking_data.class_id}, "
                    f"Client: {booking_data.client_email}"
                )
                return new_booking
                
        except HTTPException as he:
            logger.warning(
                f"Booking validation failed: {he.detail}",
                extra={'client_email': booking_data.client_email}
            )
            raise
        except Exception as e:
            db.rollback()
            logger.error(
                "Booking failed",
                exc_info=e,
                extra={
                    'class_id': booking_data.class_id,
                    'client_email': booking_data.client_email
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create booking"
            )

            
    @staticmethod
    def get_bookings_by_email(db: Session, email: str) -> List[BookingResponse]:
        print(f"DEBUG: Searching for email: {email}")  # Log the email being searched
        bookings = db.query(Booking).options(
            joinedload(Booking.fitness_class)
        ).filter(
            func.lower(Booking.client_email) == func.lower(email)
        ).all()
        return bookings
