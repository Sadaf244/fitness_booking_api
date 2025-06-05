from fastapi import FastAPI
from database import engine, Base, SessionLocal
from routers import classes, bookings
import logging
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from models import FitnessClass
from services.slot_management_service import SlotManagementService
from contextlib import contextmanager
import atexit

@contextmanager
def get_db_session():
    """Helper to create and properly close a database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def run_slot_release():
    with get_db_session() as db:
        SlotManagementService.release_slots_for_completed_classes(db)

def run_no_show_handling():
    with get_db_session() as db:
        SlotManagementService.handle_no_shows(db)

Base.metadata.create_all(bind=engine)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="Fitness Studio Booking Api",
    description="API for managing fitness class bookings",
    version="1.0.0",
)

app.include_router(classes.router)
app.include_router(bookings.router)

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    db = SessionLocal()
    try:
        with get_db_session() as db:
            if not db.query(FitnessClass).first():
                # Create sample fitness classes
                sample_classes = [
                    FitnessClass(name="Yoga Class", instructor="john Doe", start_time=utc.localize(datetime.now() + timedelta(days=1)), end_time=utc.localize(datetime.now() + timedelta(days=1,hours=1)), capacity=20, available_slots=20,status='upcoming', is_active=True),
                    FitnessClass(name="Zumba Class", instructor="Jane Smith", start_time=utc.localize(datetime.now() + timedelta(days=2)), end_time=utc.localize(datetime.now() + timedelta(days=2,hours=1)), capacity=15, available_slots=15,status='upcoming', is_active=True),
                    FitnessClass(name="Pilates Class", instructor="Alice Johnson", start_time=utc.localize(datetime.now() + timedelta(days=3)), end_time=utc.localize(datetime.now() + timedelta(days=3,hours=1)), capacity=10, available_slots=10,status='upcoming', is_active=True),
                    FitnessClass(name="HIIT Class", instructor="Bob Brown", start_time=utc.localize(datetime.now() + timedelta(days=4)), end_time=utc.localize(datetime.now() + timedelta(days=4,hours=1)), capacity=25, available_slots=25,status='upcoming', is_active=True),
                ]
                db.add_all(sample_classes)
                db.commit()
                logger.info("Sample data added")
    finally:
        db.close()
    scheduler = BackgroundScheduler()
    # Run every 15 minutes to update completed classes
    scheduler.add_job(
        run_slot_release,
        'interval',
        minutes=15,
        next_run_time=datetime.now() + timedelta(seconds=30)
    )

    # Run every 5 minutes during business hours to handle no-shows
    scheduler.add_job(
        run_no_show_handling,
        'cron',
        minute='*/5',
        hour='6-22'  # 6am to 10pm
    )
    
    scheduler.start()
    logger.info("Scheduled background tasks for slot management")
    atexit.register(lambda: scheduler.shutdown())


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutting down")