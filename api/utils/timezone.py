import pytz
from datetime import datetime

def convert_to_timezone(dt: datetime, from_tz:str, to_tz:str) -> datetime:
    try:
        if not dt.tzinfo:
            from_zone= pytz.timezone(from_tz)
            dt = from_zone.localize(dt)
        to_zone = pytz.timezone(to_tz)
        return dt.astimezone(to_zone)
    except pytz.UnknownTimeZoneError:
        logger.error(f"Unknown time zone: {from_tz} or {to_tz}")
    except AttributeError:
        logger.error(f"Invalid datetime objects provided: {e}")
