"""
Appointment-related background tasks for Easy Clinic Portal.
"""
from datetime import timedelta
from app.utils.time_helpers import get_local_time, make_aware
from app import db
from app.models.appointment import Appointment, AppointmentStatus, TimeSlot
from app.models.notification import Notification, NotificationType

def update_missed_appointments():
    """
    Update appointment statuses for missed appointments.

    This function:
    1. Finds appointments that are scheduled/rescheduled but their time has passed by more than 1 hour
    2. Updates their status to NO_SHOW
    3. Creates notifications for doctors and patients
    """
    # Get current time
    current_time = get_local_time()
    one_hour_ago = current_time - timedelta(hours=1)

    # Find appointments that are scheduled/rescheduled but their time has passed by more than 1 hour
    missed_appointments = Appointment.query.filter(
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
    ).join(TimeSlot).filter(
        TimeSlot.start_time < one_hour_ago
    ).all()

    # Make appointment times timezone-aware
    for appointment in missed_appointments:
        if appointment.time_slot.start_time.tzinfo is None:
            appointment.time_slot.start_time = make_aware(appointment.time_slot.start_time)
        if appointment.time_slot.end_time.tzinfo is None:
            appointment.time_slot.end_time = make_aware(appointment.time_slot.end_time)

    # Update appointment statuses
    for appointment in missed_appointments:
        # Update status to NO_SHOW
        appointment.status = AppointmentStatus.NO_SHOW
        appointment.notes = f"{appointment.notes or ''}\nMarked as no-show automatically at {current_time.strftime('%Y-%m-%d %H:%M')}."

        # Create notification for doctor
        doctor_notification = Notification(
            recipient_id=appointment.doctor_id,
            type=NotificationType.APPOINTMENT,
            message=f"Patient {appointment.patient.name} did not show up for appointment at {appointment.time_slot.start_time.strftime('%Y-%m-%d %H:%M')}",
            related_id=appointment.id
        )

        # Create notification for patient
        patient_notification = Notification(
            recipient_id=appointment.patient_id,
            type=NotificationType.APPOINTMENT,
            message=f"You missed your appointment with Dr. {appointment.doctor.name} at {appointment.time_slot.start_time.strftime('%Y-%m-%d %H:%M')}",
            related_id=appointment.id
        )

        db.session.add(doctor_notification)
        db.session.add(patient_notification)

    # Commit changes if any appointments were updated
    if missed_appointments:
        db.session.commit()
        print(f"Updated {len(missed_appointments)} missed appointments to NO_SHOW status.")

    return len(missed_appointments)
