"""
Time-related helper functions for Easy Clinic Portal.
"""
from datetime import datetime, timedelta
import pytz

# Set your local timezone here
LOCAL_TIMEZONE = 'Africa/Cairo'  # Example: 'America/New_York', 'Europe/London', 'Asia/Tokyo'

def get_local_time():
    """
    Get the current time in the local timezone.

    Returns:
        datetime: Current time in the local timezone
    """
    # Get current UTC time
    utc_now = datetime.utcnow()

    # Convert to local timezone
    local_tz = pytz.timezone(LOCAL_TIMEZONE)
    utc_now = pytz.utc.localize(utc_now)
    local_now = utc_now.astimezone(local_tz)

    return local_now

def make_aware(dt, timezone_name=None):
    """
    Make a naive datetime timezone-aware.

    Args:
        dt (datetime): Naive datetime object
        timezone_name (str): Timezone name (default: LOCAL_TIMEZONE)

    Returns:
        datetime: Timezone-aware datetime object
    """
    if dt is None:
        return None

    # If already timezone-aware, return as is
    if dt.tzinfo is not None:
        return dt

    # Use the specified timezone or the default
    tz_name = timezone_name or LOCAL_TIMEZONE
    tz = pytz.timezone(tz_name)

    # Make timezone-aware
    return tz.localize(dt)

def make_naive(dt):
    """
    Make a timezone-aware datetime naive by removing the timezone information.

    Args:
        dt (datetime): Timezone-aware datetime object

    Returns:
        datetime: Naive datetime object
    """
    if dt is None:
        return None

    # If already naive, return as is
    if dt.tzinfo is None:
        return dt

    # Make naive by replacing with the datetime without tzinfo
    return dt.replace(tzinfo=None)

def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Format a datetime object as a string.

    Args:
        dt (datetime): Datetime object to format
        format_str (str): Format string

    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        return ''

    return dt.strftime(format_str)

def utc_to_local(utc_dt):
    """
    Convert a UTC datetime to local timezone.

    Args:
        utc_dt (datetime): UTC datetime object

    Returns:
        datetime: Local datetime object
    """
    if utc_dt is None:
        return None

    # If the datetime is naive (no timezone info), assume it's UTC
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)

    # Convert to local timezone
    local_tz = pytz.timezone(LOCAL_TIMEZONE)
    local_dt = utc_dt.astimezone(local_tz)

    return local_dt
