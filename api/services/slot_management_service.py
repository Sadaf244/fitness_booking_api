import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from pytz import utc
from models import FitnessClass, Booking
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class SlotManagementService:
    
    @staticmethod
    def release_slots_for_completed_classes(db: Session):
        """Release slots from completed classes"""
        try:
            now = datetime.now(utc)
            cutoff_time = now - timedelta(minutes=15)
            
            classes = db.query(FitnessClass).filter(
                FitnessClass.end_time < cutoff_time,
                FitnessClass.status == 'upcoming',
                FitnessClass.is_active == True
            ).all()
            
            for cls in classes:
                attendees = db.query(Booking).filter(
                    Booking.class_id == cls.id,
                    Booking.is_cancelled == False,
                    Booking.checked_in == True
                ).count()
                
                cls.status = 'completed'
                cls.available_slots = max(0, cls.capacity - attendees)
                logger.info(f"Completed class {cls.id} with {attendees} attendees")
            
            db.commit()
            return len(classes)
            
        except Exception as e:
            logger.error(f"Error in release_slots_for_completed_classes: {str(e)}")
            if 'db' in locals():
                db.rollback()
            raise

    @staticmethod
    def handle_no_shows(db: Session):
        """Handle no-shows for ongoing classes"""
        try:
            now = datetime.now(utc)
            classes = db.query(FitnessClass).filter(
                FitnessClass.start_time < now,
                FitnessClass.end_time > now,
                FitnessClass.status == 'upcoming',
                FitnessClass.is_active == True
            ).all()
            
            for cls in classes:
                attendees = db.query(Booking).filter(
                    Booking.class_id == cls.id,
                    Booking.checked_in == True,
                    Booking.is_cancelled == False
                ).count()
                
                new_slots = max(0, cls.capacity - attendees)
                if new_slots != cls.available_slots:
                    cls.available_slots = new_slots
                    logger.info(f"Updated class {cls.id} slots to {new_slots}")
            
            db.commit()
            return len(classes)
            
        except Exception as e:
            logger.error(f"Error in handle_no_shows: {str(e)}")
            if 'db' in locals():
                db.rollback()
            raise

    @staticmethod
    def cancel_class(db: Session, class_id: int):
        """Cancel a class and all bookings"""
        try:
            cls = db.query(FitnessClass).filter(
                FitnessClass.id == class_id
            ).with_for_update().first()
            
            if not cls:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
                
            if cls.status != 'upcoming':
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Only upcoming classes can be cancelled"
                )
            
            cls.status = 'cancelled'
            cls.is_active = False
            cls.available_slots = 0
            
            db.query(Booking).filter(
                Booking.class_id == class_id,
                Booking.is_cancelled == False
            ).update({'is_cancelled': True})
            
            db.commit()
            logger.info(f"Cancelled class {class_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in cancel_class: {str(e)}")
            if 'db' in locals():
                db.rollback()
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Failed to cancel class"
            )