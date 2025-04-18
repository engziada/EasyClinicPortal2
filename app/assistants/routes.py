"""
Assistant routes for Easy Clinic Portal.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.assistants.forms import RescheduleAppointmentForm, DoctorTimeSlotForm, BulkDoctorTimeSlotForm
from app.models.user import User, Role
from app.models.appointment import Appointment, TimeSlot, AppointmentStatus
from app.models.notification import Notification, NotificationType
from app.utils.helpers import assistant_required, format_time_slot

# Create blueprint
assistants_bp = Blueprint('assistants', __name__, url_prefix='/assistants')

@assistants_bp.route('/dashboard')
@login_required
@assistant_required
def dashboard():
    """Assistant dashboard."""
    # Get upcoming appointments (both scheduled and rescheduled)
    upcoming_appointments = Appointment.query.filter(
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
    ).join(TimeSlot).filter(
        TimeSlot.start_time >= datetime.utcnow()
    ).order_by(TimeSlot.start_time).all()

    # Get doctor availability
    doctors = User.query.filter_by(role=Role.DOCTOR).all()
    doctor_availability = {}

    for doctor in doctors:
        # Count available time slots
        available_slots = TimeSlot.query.filter_by(
            doctor_id=doctor.id,
            is_booked=False
        ).filter(
            TimeSlot.start_time >= datetime.utcnow()
        ).count()

        doctor_availability[doctor.id] = {
            'name': doctor.name,
            'available_slots': available_slots
        }

    # Get recent notifications (both read and unread)
    notifications = Notification.query.filter_by(
        recipient_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        'assistants/dashboard.html',
        title='Assistant Dashboard',
        upcoming_appointments=upcoming_appointments,
        doctor_availability=doctor_availability,
        notifications=notifications
    )

@assistants_bp.route('/appointments')
@login_required
@assistant_required
def appointments():
    """View all appointments."""
    # Get all appointments
    appointments = Appointment.query.join(TimeSlot).order_by(TimeSlot.start_time.desc()).all()

    return render_template(
        'assistants/appointments.html',
        title='All Appointments',
        appointments=appointments
    )

@assistants_bp.route('/reschedule-appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@assistant_required
def reschedule_appointment(appointment_id):
    """Reschedule an appointment."""
    # Get the appointment
    appointment = Appointment.query.get_or_404(appointment_id)

    form = RescheduleAppointmentForm()

    if form.validate_on_submit():
        # Get the old time slot
        old_time_slot = TimeSlot.query.get(appointment.time_slot_id)
        old_doctor = User.query.get(appointment.doctor_id)

        # Update appointment status
        appointment.status = AppointmentStatus(form.status.data)

        if appointment.status == AppointmentStatus.CANCELLED:
            # Free up the time slot
            old_time_slot.is_booked = False
        elif appointment.status == AppointmentStatus.RESCHEDULED:
            # Get the new time slot
            new_time_slot = TimeSlot.query.get_or_404(form.time_slot.data)

            # Update appointment
            appointment.doctor_id = form.doctor.data
            appointment.time_slot_id = new_time_slot.id

            # Update time slots
            old_time_slot.is_booked = False
            new_time_slot.is_booked = True

        # Create notification for patient
        patient_notification = Notification(
            recipient_id=appointment.patient_id,
            sender_id=current_user.id,
            type=NotificationType.APPOINTMENT,
            message=f'Your appointment has been {appointment.status.value}',
            related_id=appointment.id
        )

        # Create notification for doctor if changed
        if appointment.doctor_id != old_doctor.id:
            old_doctor_notification = Notification(
                recipient_id=old_doctor.id,
                sender_id=current_user.id,
                type=NotificationType.APPOINTMENT,
                message=f'Appointment with {User.query.get(appointment.patient_id).name} has been reassigned',
                related_id=appointment.id
            )

            new_doctor_notification = Notification(
                recipient_id=appointment.doctor_id,
                sender_id=current_user.id,
                type=NotificationType.APPOINTMENT,
                message=f'New appointment assigned with {User.query.get(appointment.patient_id).name}',
                related_id=appointment.id
            )

            db.session.add(old_doctor_notification)
            db.session.add(new_doctor_notification)

        # Add to database
        db.session.add(patient_notification)
        db.session.commit()

        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('assistants.appointments'))

    # Pre-populate form with existing data
    if request.method == 'GET':
        form.doctor.data = appointment.doctor_id
        form.status.data = appointment.status.value

    return render_template(
        'assistants/reschedule_appointment.html',
        title='Reschedule Appointment',
        form=form,
        appointment=appointment
    )

@assistants_bp.route('/doctor-availability', methods=['GET', 'POST'])
@login_required
@assistant_required
def doctor_availability():
    """View and manage doctor availability."""
    # Initialize forms
    form = DoctorTimeSlotForm()
    bulk_form = BulkDoctorTimeSlotForm()

    # Handle single day time slot form submission
    if form.validate_on_submit():
        doctor_id = form.doctor.data
        date = form.date.data
        start_time_str = form.start_time.data
        end_time_str = form.end_time.data

        # Parse time strings
        start_hour, start_minute = map(int, start_time_str.split(':'))
        end_hour, end_minute = map(int, end_time_str.split(':'))

        # Create datetime objects
        start_datetime = datetime(date.year, date.month, date.day, start_hour, start_minute)
        end_datetime = datetime(date.year, date.month, date.day, end_hour, end_minute)

        # Validate time range
        if start_datetime >= end_datetime:
            flash('End time must be after start time.', 'danger')
            return redirect(url_for('assistants.doctor_availability'))

        # Create time slots (15-minute intervals)
        current_time = start_datetime
        slots_created = 0

        while current_time < end_datetime:
            next_time = current_time + timedelta(minutes=15)

            # Check if slot already exists
            existing_slot = TimeSlot.query.filter_by(
                doctor_id=doctor_id,
                start_time=current_time
            ).first()

            if not existing_slot:
                time_slot = TimeSlot(
                    doctor_id=doctor_id,
                    start_time=current_time,
                    end_time=next_time
                )
                db.session.add(time_slot)
                slots_created += 1

            current_time = next_time

        db.session.commit()

        # Create notification for doctor
        notification = Notification(
            recipient_id=doctor_id,
            sender_id=current_user.id,
            type=NotificationType.SYSTEM,
            message=f'Assistant {current_user.name} has created {slots_created} new time slots for you on {date.strftime("%Y-%m-%d")}'
        )
        db.session.add(notification)
        db.session.commit()

        flash(f'{slots_created} time slots created successfully for {User.query.get(doctor_id).name}!', 'success')
        return redirect(url_for('assistants.doctor_availability'))

    # Get all doctors
    doctors = User.query.filter_by(role=Role.DOCTOR).all()

    # Get availability for each doctor
    availability = {}

    for doctor in doctors:
        # Get available time slots
        available_slots = TimeSlot.query.filter_by(
            doctor_id=doctor.id,
            is_booked=False
        ).filter(
            TimeSlot.start_time >= datetime.utcnow()
        ).order_by(TimeSlot.start_time).all()

        # Group time slots by date for better display
        grouped_slots = {}
        for slot in available_slots:
            date_str = slot.start_time.strftime('%Y-%m-%d')
            if date_str not in grouped_slots:
                grouped_slots[date_str] = []
            grouped_slots[date_str].append(slot)

        availability[doctor.id] = {
            'name': doctor.name,
            'slots': available_slots,
            'grouped_slots': grouped_slots,
            'total_slots': len(available_slots)
        }

    return render_template(
        'assistants/doctor_availability.html',
        title='Doctor Availability',
        availability=availability,
        form=form,
        bulk_form=bulk_form,
        format_time_slot=format_time_slot
    )

@assistants_bp.route('/bulk-time-slots', methods=['POST'])
@login_required
@assistant_required
def bulk_time_slots():
    """Create bulk time slots for a doctor."""
    form = BulkDoctorTimeSlotForm()

    if form.validate_on_submit():
        doctor_id = form.doctor.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        days_of_week = [int(day) for day in form.days_of_week.data]
        start_time_str = form.start_time.data
        end_time_str = form.end_time.data

        # Parse time strings
        start_hour, start_minute = map(int, start_time_str.split(':'))
        end_hour, end_minute = map(int, end_time_str.split(':'))

        # Validate date range
        if start_date > end_date:
            flash('End date must be after start date.', 'danger')
            return redirect(url_for('assistants.doctor_availability'))

        # Create time slots for each day in the range that matches the selected days of week
        current_date = start_date
        slots_created = 0

        while current_date <= end_date:
            # Check if current day is in selected days of week (0 = Monday, 6 = Sunday)
            if current_date.weekday() in days_of_week:
                # Create start and end datetime objects for this day
                start_datetime = datetime(current_date.year, current_date.month, current_date.day, start_hour, start_minute)
                end_datetime = datetime(current_date.year, current_date.month, current_date.day, end_hour, end_minute)

                # Create time slots for this day
                current_time = start_datetime
                while current_time < end_datetime:
                    next_time = current_time + timedelta(minutes=15)

                    # Check if slot already exists
                    existing_slot = TimeSlot.query.filter_by(
                        doctor_id=doctor_id,
                        start_time=current_time
                    ).first()

                    if not existing_slot:
                        time_slot = TimeSlot(
                            doctor_id=doctor_id,
                            start_time=current_time,
                            end_time=next_time
                        )
                        db.session.add(time_slot)
                        slots_created += 1

                    current_time = next_time

            # Move to next day
            current_date += timedelta(days=1)

        db.session.commit()

        # Create notification for doctor
        notification = Notification(
            recipient_id=doctor_id,
            sender_id=current_user.id,
            type=NotificationType.SYSTEM,
            message=f'Assistant {current_user.name} has created {slots_created} new time slots for you between {start_date.strftime("%Y-%m-%d")} and {end_date.strftime("%Y-%m-%d")}'
        )
        db.session.add(notification)
        db.session.commit()

        flash(f'{slots_created} time slots created successfully for {User.query.get(doctor_id).name}!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('assistants.doctor_availability'))

@assistants_bp.route('/delete-time-slot/<int:slot_id>', methods=['POST'])
@login_required
@assistant_required
def delete_time_slot(slot_id):
    """Delete a time slot."""
    # Get the time slot
    time_slot = TimeSlot.query.get_or_404(slot_id)

    # Check if the time slot is booked
    if time_slot.is_booked:
        flash('Cannot delete a booked time slot.', 'danger')
        return redirect(url_for('assistants.doctor_availability'))

    # Get the doctor for notification
    doctor_id = time_slot.doctor_id
    slot_time = time_slot.start_time.strftime('%Y-%m-%d %H:%M')

    # Delete the time slot
    db.session.delete(time_slot)

    # Create notification for doctor
    notification = Notification(
        recipient_id=doctor_id,
        sender_id=current_user.id,
        type=NotificationType.SYSTEM,
        message=f'Assistant {current_user.name} has deleted your time slot at {slot_time}'
    )
    db.session.add(notification)
    db.session.commit()

    flash('Time slot deleted successfully!', 'success')
    return redirect(url_for('assistants.doctor_availability'))

@assistants_bp.route('/delete-day-slots/<int:doctor_id>/<string:date_str>', methods=['POST'])
@login_required
@assistant_required
def delete_day_slots(doctor_id, date_str):
    """Delete all time slots for a specific day and doctor."""
    try:
        # Parse the date string
        year, month, day = map(int, date_str.split('-'))
        date = datetime(year, month, day).date()

        # Get all time slots for this day
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = datetime.combine(date, datetime.max.time())

        # Find all unbooked time slots for this day
        time_slots = TimeSlot.query.filter(
            TimeSlot.doctor_id == doctor_id,
            TimeSlot.start_time >= start_datetime,
            TimeSlot.start_time < end_datetime,
            TimeSlot.is_booked == False
        ).all()

        # Delete the time slots
        slots_deleted = 0
        for slot in time_slots:
            db.session.delete(slot)
            slots_deleted += 1

        # Create notification for doctor
        if slots_deleted > 0:
            notification = Notification(
                recipient_id=doctor_id,
                sender_id=current_user.id,
                type=NotificationType.SYSTEM,
                message=f'Assistant {current_user.name} has deleted {slots_deleted} of your time slots on {date_str}'
            )
            db.session.add(notification)

        db.session.commit()

        flash(f'{slots_deleted} time slots deleted successfully!', 'success')
    except ValueError:
        flash('Invalid date format.', 'danger')

    return redirect(url_for('assistants.doctor_availability'))

@assistants_bp.route('/notifications')
@login_required
@assistant_required
def notifications():
    """View all notifications."""
    # Get all notifications
    notifications = Notification.query.filter_by(
        recipient_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()

    # Mark notifications as read
    for notification in notifications:
        notification.is_read = True

    db.session.commit()

    return render_template(
        'assistants/notifications.html',
        title='My Notifications',
        notifications=notifications
    )

@assistants_bp.route('/get-time-slots/<int:doctor_id>')
@login_required
@assistant_required
def get_time_slots(doctor_id):
    """AJAX endpoint to get available time slots for a doctor."""
    # Get available time slots
    time_slots = TimeSlot.query.filter_by(
        doctor_id=doctor_id,
        is_booked=False
    ).filter(
        TimeSlot.start_time >= datetime.utcnow()
    ).order_by(TimeSlot.start_time).all()

    # Format for select field
    time_slot_list = [
        {
            'id': slot.id,
            'text': slot.start_time.strftime('%Y-%m-%d %H:%M')
        }
        for slot in time_slots
    ]

    return {'time_slots': time_slot_list}
