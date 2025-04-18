"""
Patient routes for Easy Clinic Portal.
"""
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.patients.forms import ProfileForm, AppointmentForm, ImageUploadForm, RescheduleAppointmentForm, CancelAppointmentForm
from app.models.user import User, Role
from app.models.appointment import Appointment, TimeSlot, AppointmentStatus
from app.models.image import ImageUpload
from app.models.notification import Notification, NotificationType
from app.utils.helpers import patient_required

# Create blueprint
patients_bp = Blueprint('patients', __name__, url_prefix='/patients')

@patients_bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    """Patient dashboard."""
    # Get upcoming appointments (both scheduled and rescheduled)
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == current_user.id,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
    ).join(TimeSlot).filter(
        TimeSlot.start_time >= datetime.utcnow()
    ).order_by(TimeSlot.start_time).all()

    # Get recent image uploads
    recent_uploads = ImageUpload.query.filter_by(
        patient_id=current_user.id
    ).order_by(ImageUpload.created_at.desc()).limit(5).all()

    # Get unread notifications
    notifications = Notification.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()

    return render_template(
        'patients/dashboard.html',
        title='Patient Dashboard',
        upcoming_appointments=upcoming_appointments,
        recent_uploads=recent_uploads,
        notifications=notifications
    )

@patients_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@patient_required
def profile():
    """Patient profile management."""
    form = ProfileForm()

    if form.validate_on_submit():
        # Update profile information
        profile = current_user.patient_profile
        profile.date_of_birth = form.date_of_birth.data
        profile.gender = form.gender.data
        profile.phone = form.phone.data
        profile.address = form.address.data
        profile.medical_history = form.medical_history.data
        profile.allergies = form.allergies.data

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patients.profile'))

    # Pre-populate form with existing data
    if request.method == 'GET' and current_user.patient_profile:
        form.date_of_birth.data = current_user.patient_profile.date_of_birth
        form.gender.data = current_user.patient_profile.gender
        form.phone.data = current_user.patient_profile.phone
        form.address.data = current_user.patient_profile.address
        form.medical_history.data = current_user.patient_profile.medical_history
        form.allergies.data = current_user.patient_profile.allergies

    return render_template('patients/profile.html', title='My Profile', form=form)

@patients_bp.route('/reserve-appointment', methods=['GET', 'POST'])
@login_required
@patient_required
def reserve_appointment():
    """Reserve an appointment with a doctor."""
    form = AppointmentForm()

    # If the form is submitted, populate the time_slot choices based on the selected doctor
    if request.method == 'POST' and form.doctor.data:
        # Check if patient already has an active appointment with this doctor
        existing_appointment = Appointment.query.filter(
            Appointment.patient_id == current_user.id,
            Appointment.doctor_id == form.doctor.data,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
        ).first()

        if existing_appointment:
            flash(f'You already have an active appointment with Dr. {User.query.get(form.doctor.data).name} on {existing_appointment.time_slot.start_time.strftime("%Y-%m-%d %H:%M")}. Please cancel or reschedule it before making a new one.', 'warning')
            return redirect(url_for('patients.appointments'))

        # Get available time slots for the selected doctor
        time_slots = TimeSlot.query.filter_by(
            doctor_id=form.doctor.data,
            is_booked=False
        ).filter(
            TimeSlot.start_time >= datetime.utcnow()
        ).order_by(TimeSlot.start_time).all()

        # Update the time_slot choices
        form.time_slot.choices = [(slot.id, slot.start_time.strftime('%Y-%m-%d %H:%M')) for slot in time_slots]

        # If no time slots are available, add a dummy option
        if not time_slots:
            form.time_slot.choices = [(-1, 'No available time slots')]
            flash('No available time slots for the selected doctor.', 'warning')

    # Validate the form after setting the choices
    if request.method == 'POST' and form.validate():
        # Get the selected time slot
        time_slot = TimeSlot.query.get_or_404(form.time_slot.data)

        # Check if time slot is still available
        if time_slot.is_booked:
            flash('This time slot is no longer available. Please select another.', 'danger')
            return redirect(url_for('patients.reserve_appointment'))

        # Check if patient already has an appointment at this time with any doctor
        # First, get all active appointments for this patient
        patient_appointments = Appointment.query.filter(
            Appointment.patient_id == current_user.id,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
        ).join(TimeSlot).all()

        # Check for time conflicts
        for existing_appointment in patient_appointments:
            existing_slot = existing_appointment.time_slot
            # Check if the time slots overlap
            if (existing_slot.start_time <= time_slot.end_time and
                existing_slot.end_time >= time_slot.start_time):
                doctor_name = User.query.get(existing_appointment.doctor_id).name
                flash(f'You already have an appointment with Dr. {doctor_name} at {existing_slot.start_time.strftime("%Y-%m-%d %H:%M")}. You cannot book overlapping appointments.', 'danger')
                return redirect(url_for('patients.reserve_appointment'))

        # Create new appointment
        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=form.doctor.data,
            time_slot_id=time_slot.id,
            reason=form.reason.data,
            status=AppointmentStatus.SCHEDULED
        )

        # Mark time slot as booked
        time_slot.is_booked = True

        # Create notifications
        doctor_notification = Notification(
            recipient_id=form.doctor.data,
            sender_id=current_user.id,
            type=NotificationType.APPOINTMENT,
            message=f'New appointment scheduled with {current_user.name} on {time_slot.start_time.strftime("%Y-%m-%d %H:%M")}',
            related_id=appointment.id
        )

        assistant_notification = Notification(
            recipient_id=User.query.filter_by(role=Role.ASSISTANT).first().id,
            sender_id=current_user.id,
            type=NotificationType.APPOINTMENT,
            message=f'New appointment scheduled: {current_user.name} with Dr. {User.query.get(form.doctor.data).name}',
            related_id=appointment.id
        )

        # Add to database
        db.session.add(appointment)
        db.session.add(doctor_notification)
        db.session.add(assistant_notification)
        db.session.commit()

        flash('Appointment scheduled successfully!', 'success')
        return redirect(url_for('patients.dashboard'))

    return render_template('patients/reserve_appointment.html', title='Reserve Appointment', form=form)

@patients_bp.route('/upload-image', methods=['GET', 'POST'])
@login_required
@patient_required
def upload_image():
    """Upload symptom image to a doctor."""
    form = ImageUploadForm()

    if form.validate_on_submit():
        # Save the uploaded image
        image_file = form.image.data
        filename = secure_filename(image_file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        filename = f"{current_user.id}_{timestamp}_{filename}"

        # Ensure upload directory exists
        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'images')
        os.makedirs(upload_dir, exist_ok=True)

        # Save the file
        image_path = os.path.join(upload_dir, filename)
        image_file.save(image_path)

        # Create database record
        relative_path = f'uploads/images/{filename}'
        image_upload = ImageUpload(
            patient_id=current_user.id,
            doctor_id=form.doctor.data,
            image_path=relative_path,
            message=form.message.data
        )

        # Create notification for doctor
        notification = Notification(
            recipient_id=form.doctor.data,
            sender_id=current_user.id,
            type=NotificationType.IMAGE_UPLOAD,
            message=f'New symptom image uploaded by {current_user.name}',
            related_id=image_upload.id
        )

        # Add to database
        db.session.add(image_upload)
        db.session.add(notification)
        db.session.commit()

        flash('Image uploaded successfully!', 'success')
        return redirect(url_for('patients.dashboard'))

    return render_template('patients/upload_image.html', title='Upload Symptom Image', form=form)

@patients_bp.route('/appointments')
@login_required
@patient_required
def appointments():
    """View all appointments."""
    # Get all appointments
    all_appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).join(TimeSlot).all()

    # Calculate the minimum time for editable appointments (1 hour from now)
    min_edit_time = datetime.utcnow() + timedelta(hours=1)

    # Separate upcoming and past appointments
    upcoming_appointments = []
    past_appointments = []

    for appointment in all_appointments:
        # Only consider scheduled and rescheduled appointments as upcoming
        is_active = appointment.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED]
        is_future = appointment.time_slot.start_time >= datetime.utcnow()

        if is_future and is_active:
            upcoming_appointments.append(appointment)
        else:
            past_appointments.append(appointment)

    # Sort upcoming appointments by start time (ascending)
    upcoming_appointments.sort(key=lambda x: x.time_slot.start_time)

    # Sort past appointments by start time (descending)
    past_appointments.sort(key=lambda x: x.time_slot.start_time, reverse=True)

    return render_template(
        'patients/appointments.html',
        title='My Appointments',
        upcoming_appointments=upcoming_appointments,
        past_appointments=past_appointments,
        min_edit_time=min_edit_time,
        now=datetime.utcnow()
    )

@patients_bp.route('/cancel-appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@patient_required
def cancel_appointment(appointment_id):
    """Cancel an appointment."""
    # Get the appointment
    appointment = Appointment.query.filter(
        Appointment.id == appointment_id,
        Appointment.patient_id == current_user.id,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
    ).first_or_404()

    # Check if appointment is at least 1 hour in the future
    min_edit_time = datetime.utcnow() + timedelta(hours=1)
    if appointment.time_slot.start_time <= min_edit_time:
        flash('You can only cancel appointments that are at least 1 hour in the future.', 'danger')
        return redirect(url_for('patients.appointments'))

    form = CancelAppointmentForm()

    if form.validate_on_submit():
        # Get the time slot
        time_slot = TimeSlot.query.get(appointment.time_slot_id)

        # Update appointment status
        appointment.status = AppointmentStatus.CANCELLED
        appointment.notes = form.reason.data if form.reason.data else 'Cancelled by patient'

        # Free up the time slot
        time_slot.is_booked = False

        # Create notifications
        doctor_notification = Notification(
            recipient_id=appointment.doctor_id,
            sender_id=current_user.id,
            type=NotificationType.APPOINTMENT,
            message=f'Appointment with {current_user.name} on {time_slot.start_time.strftime("%Y-%m-%d %H:%M")} has been cancelled.',
            related_id=appointment.id
        )

        assistant_notification = Notification(
            recipient_id=User.query.filter_by(role=Role.ASSISTANT).first().id,
            sender_id=current_user.id,
            type=NotificationType.APPOINTMENT,
            message=f'Appointment cancelled: {current_user.name} with Dr. {appointment.doctor.name}',
            related_id=appointment.id
        )

        # Add to database
        db.session.add(doctor_notification)
        db.session.add(assistant_notification)
        db.session.commit()

        flash('Appointment cancelled successfully!', 'success')
        return redirect(url_for('patients.appointments'))

    return render_template(
        'patients/cancel_appointment.html',
        title='Cancel Appointment',
        form=form,
        appointment=appointment
    )

@patients_bp.route('/reschedule-appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@patient_required
def reschedule_appointment(appointment_id):
    """Reschedule an appointment."""
    # Get the appointment
    appointment = Appointment.query.filter(
        Appointment.id == appointment_id,
        Appointment.patient_id == current_user.id,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
    ).first_or_404()

    # Check if appointment is at least 1 hour in the future
    min_edit_time = datetime.utcnow() + timedelta(hours=1)
    if appointment.time_slot.start_time <= min_edit_time:
        flash('You can only reschedule appointments that are at least 1 hour in the future.', 'danger')
        return redirect(url_for('patients.appointments'))

    # Get available time slots for the doctor
    available_slots = TimeSlot.query.filter_by(
        doctor_id=appointment.doctor_id,
        is_booked=False
    ).filter(
        TimeSlot.start_time >= datetime.utcnow() + timedelta(hours=1)
    ).order_by(TimeSlot.start_time).all()

    # Create form and populate time slot choices
    form = RescheduleAppointmentForm()
    form.time_slot.choices = [(slot.id, slot.start_time.strftime('%Y-%m-%d %H:%M')) for slot in available_slots]

    if request.method == 'GET':
        form.appointment_id.data = appointment.id

    if form.validate_on_submit():
        # Get the old and new time slots
        old_time_slot = TimeSlot.query.get(appointment.time_slot_id)
        new_time_slot = TimeSlot.query.get_or_404(form.time_slot.data)

        # Check if new time slot is still available
        if new_time_slot.is_booked:
            flash('This time slot is no longer available. Please select another.', 'danger')
            return redirect(url_for('patients.reschedule_appointment', appointment_id=appointment.id))

        # Check if patient already has another appointment at this time with any doctor
        # First, get all active appointments for this patient (excluding the current one being rescheduled)
        patient_appointments = Appointment.query.filter(
            Appointment.patient_id == current_user.id,
            Appointment.id != appointment.id,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
        ).join(TimeSlot).all()

        # Check for time conflicts
        for existing_appointment in patient_appointments:
            existing_slot = existing_appointment.time_slot
            # Check if the time slots overlap
            if (existing_slot.start_time <= new_time_slot.end_time and
                existing_slot.end_time >= new_time_slot.start_time):
                doctor_name = User.query.get(existing_appointment.doctor_id).name
                flash(f'You already have an appointment with Dr. {doctor_name} at {existing_slot.start_time.strftime("%Y-%m-%d %H:%M")}. You cannot book overlapping appointments.', 'danger')
                return redirect(url_for('patients.reschedule_appointment', appointment_id=appointment.id))

        # Update appointment
        appointment.time_slot_id = new_time_slot.id
        appointment.status = AppointmentStatus.RESCHEDULED
        appointment.notes = form.reason.data if form.reason.data else 'Rescheduled by patient'

        # Update time slots
        old_time_slot.is_booked = False
        new_time_slot.is_booked = True

        # Create notifications
        doctor_notification = Notification(
            recipient_id=appointment.doctor_id,
            sender_id=current_user.id,
            type=NotificationType.APPOINTMENT,
            message=f'Appointment with {current_user.name} has been rescheduled to {new_time_slot.start_time.strftime("%Y-%m-%d %H:%M")}.',
            related_id=appointment.id
        )

        assistant_notification = Notification(
            recipient_id=User.query.filter_by(role=Role.ASSISTANT).first().id,
            sender_id=current_user.id,
            type=NotificationType.APPOINTMENT,
            message=f'Appointment rescheduled: {current_user.name} with Dr. {appointment.doctor.name}',
            related_id=appointment.id
        )

        # Add to database
        db.session.add(doctor_notification)
        db.session.add(assistant_notification)
        db.session.commit()

        flash('Appointment rescheduled successfully!', 'success')
        return redirect(url_for('patients.appointments'))

    # Check if there are available slots
    has_available_slots = len(form.time_slot.choices) > 0

    return render_template(
        'patients/reschedule_appointment.html',
        title='Reschedule Appointment',
        form=form,
        appointment=appointment,
        has_available_slots=has_available_slots
    )

@patients_bp.route('/get-available-slots/<int:doctor_id>/<int:appointment_id>')
@login_required
@patient_required
def get_available_slots(doctor_id, appointment_id):
    """AJAX endpoint to get available time slots for rescheduling."""
    # Get available time slots
    time_slots = TimeSlot.query.filter_by(
        doctor_id=doctor_id,
        is_booked=False
    ).filter(
        TimeSlot.start_time >= datetime.utcnow() + timedelta(hours=1)
    ).order_by(TimeSlot.start_time).all()

    # Format for select field
    time_slot_list = [
        {
            'id': slot.id,
            'text': slot.start_time.strftime('%Y-%m-%d %H:%M')
        }
        for slot in time_slots
    ]

    return jsonify({'time_slots': time_slot_list})

@patients_bp.route('/uploads')
@login_required
@patient_required
def uploads():
    """View all image uploads."""
    # Get all image uploads
    uploads = ImageUpload.query.filter_by(
        patient_id=current_user.id
    ).order_by(ImageUpload.created_at.desc()).all()

    return render_template(
        'patients/uploads.html',
        title='My Uploads',
        uploads=uploads
    )

@patients_bp.route('/notifications')
@login_required
@patient_required
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
        'patients/notifications.html',
        title='My Notifications',
        notifications=notifications
    )

@patients_bp.route('/get-time-slots/<int:doctor_id>')
@login_required
@patient_required
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
