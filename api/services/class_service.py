from sqlalchemy.orm import Session
from models import FitnessClass
from schemas import FitnessClassCreate, FitnessClassResponse
from utils.timezone import convert_to_timezone
from typing import List
import logging
from functools import lru_cache
logger = logging.getLogger(__name__)

class ClassService:
    @staticmethod
    @lru_cache(maxsize=32)
    def get_all_classes(db: Session, timezone: str=None) -> List[FitnessClassResponse]:
        classes = db.query(FitnessClass).all()
        if timezone:
            for cls in classes:
                cls.start_time = convert_to_timezone(cls.start_time, cls.timezone, timezone)
                cls.end_time = convert_to_timezone(cls.end_time, cls.timezone, timezone)
        return classes

    @staticmethod
    def get_class(db: Session, class_id: int) -> FitnessClass:
        return db.query(FitnessClass).filter(FitnessClass.id == class_id).first()


    @staticmethod
    def reserve_slot(db: Session, class_id: int) -> bool:
        try:            # Use with_for_update to lock the row for update
            fitness_class = db.query(FitnessClass).filter(FitnessClass.id == class_id).with_for_update().first()
            with db.begin_nested():
                fitness_class = db.query(FitnessClass).filter(FitnessClass.id == class_id).with_for_update().first()
                if not fitness_class or fitness_class.available_slots <= 0:
                    return False
                fitness_class.available_slots -= 1
            db.commit()
            return True
        except:
            db.rollback()
            logger.error(f"Failed to decrease available slots for class {class_id}")
            return False

    @staticmethod
    def update_class(db: Session, class_id: int, update_data: dict):
        fitness_class = db.query(FitnessClass).get(class_id)
        if not fitness_class:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Prevent modifying class that has already started
        if fitness_class.start_time < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify a class that has already started"
            )
        
        # Prevent reducing capacity below current bookings
        if 'capacity' in update_data:
            current_bookings = db.query(Booking).filter_by(class_id=class_id).count()
            if update_data['capacity'] < current_bookings:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot reduce capacity below current bookings ({current_bookings})"
                )
            update_data['available_slots'] = update_data['capacity'] - current_bookings

    