"""
Helper functions for Easy Clinic Portal.
"""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from app.models.user import Role
from datetime import datetime, timedelta

def patient_required(f):
    """
    Decorator for views that require patient role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_patient():
            flash('This page is only accessible to patients.', 'danger')
            if current_user.is_doctor():
                return redirect(url_for('doctors.dashboard'))
            elif current_user.is_assistant():
                return redirect(url_for('assistants.dashboard'))
            elif current_user.is_admin() or current_user.is_superadmin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    """
    Decorator for views that require doctor role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_doctor():
            flash('This page is only accessible to doctors.', 'danger')
            if current_user.is_patient():
                return redirect(url_for('patients.dashboard'))
            elif current_user.is_assistant():
                return redirect(url_for('assistants.dashboard'))
            elif current_user.is_admin() or current_user.is_superadmin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def assistant_required(f):
    """
    Decorator for views that require assistant role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_assistant():
            flash('This page is only accessible to assistants.', 'danger')
            if current_user.is_patient():
                return redirect(url_for('patients.dashboard'))
            elif current_user.is_doctor():
                return redirect(url_for('doctors.dashboard'))
            elif current_user.is_admin() or current_user.is_superadmin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator for views that require admin or superadmin role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.is_admin() or current_user.is_superadmin()):
            flash('This page is only accessible to administrators.', 'danger')
            if current_user.is_patient():
                return redirect(url_for('patients.dashboard'))
            elif current_user.is_doctor():
                return redirect(url_for('doctors.dashboard'))
            elif current_user.is_assistant():
                return redirect(url_for('assistants.dashboard'))
            else:
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename, allowed_extensions):
    """
    Check if a file has an allowed extension.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def staff_required(f):
    """
    Decorator for views that require staff roles (doctor, assistant, admin, or superadmin).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_patient():
            flash('This page is only accessible to staff members.', 'danger')
            return redirect(url_for('patients.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def generate_time_slots(date, doctor_id):
    """
    Generate time slots for a given date between 10:00 AM and 10:00 PM with 15-minute intervals.

    Args:
        date (datetime.date): The date to generate time slots for
        doctor_id (int): The ID of the doctor

    Returns:
        list: A list of dictionaries containing start_time and end_time for each slot
    """
    time_slots = []

    # Start time: 10:00 AM
    start_hour = 10
    # End time: 10:00 PM
    end_hour = 22

    # Create a datetime object for the start of the day
    start_datetime = datetime.combine(date, datetime.min.time())
    start_datetime = start_datetime.replace(hour=start_hour, minute=0, second=0)

    # Create a datetime object for the end of the day
    end_datetime = start_datetime.replace(hour=end_hour, minute=0, second=0)

    # Generate time slots with 15-minute intervals
    current_time = start_datetime
    while current_time < end_datetime:
        next_time = current_time + timedelta(minutes=15)

        time_slots.append({
            'doctor_id': doctor_id,
            'start_time': current_time,
            'end_time': next_time
        })

        current_time = next_time

    return time_slots

def format_time_slot(time_slot):
    """
    Format a time slot for display.

    Args:
        time_slot: TimeSlot object

    Returns:
        str: Formatted time slot string
    """
    return f"{time_slot.start_time.strftime('%Y-%m-%d %H:%M')} - {time_slot.end_time.strftime('%H:%M')}"
