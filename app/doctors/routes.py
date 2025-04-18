"""
Doctor routes for Easy Clinic Portal.
"""
import os
from datetime import datetime, timedelta
from app.utils.time_helpers import get_local_time, utc_to_local, make_aware, make_naive
from app.utils.ml_model import predict_skin_disease, resize_image_to_300x300
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.doctors.forms import DiagnosticForm, LiveInspectionForm, ProfileForm, TimeSlotForm, BulkTimeSlotForm
from app.models.user import User, Role, DoctorProfile
from app.models.appointment import Appointment, TimeSlot, AppointmentStatus
from app.models.image import ImageUpload, DiagnosticRecord
from app.models.notification import Notification, NotificationType
from app.utils.helpers import doctor_required, generate_time_slots, format_time_slot

# Create blueprint
doctors_bp = Blueprint('doctors', __name__, url_prefix='/doctors')

@doctors_bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    """Doctor dashboard."""
    # Get today's appointments
    today = get_local_time().date()
    tomorrow = today + timedelta(days=1)

    today_appointments = Appointment.query.filter_by(
        doctor_id=current_user.id,
        status=AppointmentStatus.SCHEDULED
    ).join(TimeSlot).filter(
        TimeSlot.start_time >= today,
        TimeSlot.start_time < tomorrow
    ).order_by(TimeSlot.start_time).all()

    # Get unreviewed image uploads
    unreviewed_uploads = ImageUpload.query.filter_by(
        doctor_id=current_user.id,
        is_reviewed=False
    ).order_by(ImageUpload.created_at.desc()).all()

    # Get unread notifications
    notifications = Notification.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()

    # Get current time for template
    current_time = get_local_time()

    # Make appointment times timezone-aware
    for appointment in today_appointments:
        if appointment.time_slot.start_time.tzinfo is None:
            appointment.time_slot.start_time = make_aware(appointment.time_slot.start_time)
        if appointment.time_slot.end_time.tzinfo is None:
            appointment.time_slot.end_time = make_aware(appointment.time_slot.end_time)

    return render_template(
        'doctors/dashboard.html',
        title='Doctor Dashboard',
        today_appointments=today_appointments,
        unreviewed_uploads=unreviewed_uploads,
        notifications=notifications,
        now=current_time
    )

@doctors_bp.route('/profile')
@login_required
@doctor_required
def profile():
    """View doctor profile (read-only)."""
    # Get doctor profile
    doctor_profile = current_user.doctor_profile

    return render_template(
        'doctors/profile.html',
        title='My Profile',
        doctor_profile=doctor_profile
    )

@doctors_bp.route('/live-inspection/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@doctor_required
def live_inspection(appointment_id):
    """Live inspection screen for appointments."""
    # Get the appointment
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=current_user.id
    ).first_or_404()

    # Get the patient
    patient = User.query.get_or_404(appointment.patient_id)

    form = LiveInspectionForm()

    if form.validate_on_submit():
        # Create diagnostic record
        diagnostic = DiagnosticRecord(
            doctor_id=current_user.id,
            patient_id=patient.id,
            appointment_id=appointment.id,
            notes=form.notes.data,
            prescriptions=form.prescriptions.data,
            recommendations=form.recommendations.data,
            red_flag=form.red_flag.data
        )

        # Handle image uploads
        if form.images.data:
            for image_file in request.files.getlist('images'):
                if image_file.filename:
                    filename = secure_filename(image_file.filename)
                    timestamp = get_local_time().strftime('%Y%m%d%H%M%S')
                    filename = f"live_{appointment.id}_{timestamp}_{filename}"

                    # Ensure upload directory exists
                    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'images')
                    os.makedirs(upload_dir, exist_ok=True)

                    # Save the file
                    image_path = os.path.join(upload_dir, filename)
                    image_file.save(image_path)

                    # Create database record
                    relative_path = f'uploads/images/{filename}'
                    image_upload = ImageUpload(
                        patient_id=patient.id,
                        doctor_id=current_user.id,
                        image_path=relative_path,
                        message="Uploaded during live inspection",
                        is_reviewed=True
                    )

                    db.session.add(image_upload)

        # Update appointment status
        appointment.status = AppointmentStatus.COMPLETED

        # Create notification for patient
        notification = Notification(
            recipient_id=patient.id,
            sender_id=current_user.id,
            type=NotificationType.DIAGNOSTIC,
            message=f'Your appointment with Dr. {current_user.name} has been completed',
            related_id=diagnostic.id
        )

        # Add to database
        db.session.add(diagnostic)
        db.session.add(notification)
        db.session.commit()

        flash('Inspection completed successfully!', 'success')
        return redirect(url_for('doctors.dashboard'))

    return render_template(
        'doctors/live_inspection.html',
        title='Live Inspection',
        form=form,
        appointment=appointment,
        patient=patient
    )

@doctors_bp.route('/upload-requests')
@login_required
@doctor_required
def upload_requests():
    """View image upload requests."""
    # Get all unreviewed image uploads
    uploads = ImageUpload.query.filter_by(
        doctor_id=current_user.id,
        is_reviewed=False
    ).order_by(ImageUpload.created_at.desc()).all()

    return render_template(
        'doctors/upload_requests.html',
        title='Upload Requests',
        uploads=uploads
    )

@doctors_bp.route('/review-upload/<int:upload_id>', methods=['GET', 'POST'])
@login_required
@doctor_required
def review_upload(upload_id):
    """Review an image upload."""
    # Get the image upload
    upload = ImageUpload.query.filter_by(
        id=upload_id,
        doctor_id=current_user.id
    ).first_or_404()

    # Get the patient
    patient = User.query.get_or_404(upload.patient_id)

    # Ensure the image is 300x300 for ML model
    image_path = os.path.join(current_app.static_folder, upload.image_path)
    resize_image_to_300x300(image_path)

    form = DiagnosticForm()

    if form.validate_on_submit():
        # Create diagnostic record
        diagnostic = DiagnosticRecord(
            doctor_id=current_user.id,
            patient_id=patient.id,
            image_id=upload.id,
            notes=form.notes.data,
            prescriptions=form.prescriptions.data,
            recommendations=form.recommendations.data,
            red_flag=form.red_flag.data
        )

        # Mark upload as reviewed
        upload.is_reviewed = True

        # Create notification for patient
        notification = Notification(
            recipient_id=patient.id,
            sender_id=current_user.id,
            type=NotificationType.DIAGNOSTIC,
            message=f'Dr. {current_user.name} has reviewed your uploaded image',
            related_id=diagnostic.id
        )

        # Add to database
        db.session.add(diagnostic)
        db.session.add(notification)
        db.session.commit()

        flash('Image reviewed successfully!', 'success')
        return redirect(url_for('doctors.upload_requests'))

    return render_template(
        'doctors/review_upload.html',
        title='Review Upload',
        form=form,
        upload=upload,
        patient=patient
    )

@doctors_bp.route('/appointments')
@login_required
@doctor_required
def appointments():
    """View all appointments."""
    # Get all appointments
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.id
    ).join(TimeSlot).order_by(TimeSlot.start_time.desc()).all()

    # Get current time for template
    current_time = get_local_time()

    # Make appointment times timezone-aware
    for appointment in appointments:
        if appointment.time_slot.start_time.tzinfo is None:
            appointment.time_slot.start_time = make_aware(appointment.time_slot.start_time)
        if appointment.time_slot.end_time.tzinfo is None:
            appointment.time_slot.end_time = make_aware(appointment.time_slot.end_time)

    return render_template(
        'doctors/appointments.html',
        title='My Appointments',
        appointments=appointments,
        now=current_time
    )

@doctors_bp.route('/patient/<int:patient_id>')
@login_required
@doctor_required
def patient_details(patient_id):
    """View detailed patient information."""
    # Get the patient
    patient = User.query.filter_by(id=patient_id, role=Role.PATIENT).first_or_404()

    # Get patient profile
    patient_profile = patient.patient_profile

    # Get past appointments with this doctor
    past_appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).filter(
        Appointment.status.in_([AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW])
    ).join(TimeSlot).order_by(TimeSlot.start_time.desc()).all()

    # Get upcoming appointments with this doctor
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).filter(
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
    ).join(TimeSlot).order_by(TimeSlot.start_time).all()

    # Get diagnostic records for this patient by this doctor
    diagnostic_records = DiagnosticRecord.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).order_by(DiagnosticRecord.created_at.desc()).all()

    # Get image uploads from this patient to this doctor
    image_uploads = ImageUpload.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).order_by(ImageUpload.created_at.desc()).all()

    # Get current time for template
    current_time = get_local_time()

    # Make appointment times timezone-aware
    for appointment in past_appointments + upcoming_appointments:
        if appointment.time_slot.start_time.tzinfo is None:
            appointment.time_slot.start_time = make_aware(appointment.time_slot.start_time)
        if appointment.time_slot.end_time.tzinfo is None:
            appointment.time_slot.end_time = make_aware(appointment.time_slot.end_time)

    return render_template(
        'doctors/patient_details.html',
        title=f'Patient: {patient.name}',
        patient=patient,
        patient_profile=patient_profile,
        past_appointments=past_appointments,
        upcoming_appointments=upcoming_appointments,
        diagnostic_records=diagnostic_records,
        image_uploads=image_uploads,
        now=current_time
    )

@doctors_bp.route('/time-slots', methods=['GET', 'POST'])
@login_required
@doctor_required
def time_slots():
    """Manage time slots."""
    form = TimeSlotForm()
    bulk_form = BulkTimeSlotForm()

    if form.validate_on_submit():
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
            return redirect(url_for('doctors.time_slots'))

        # Create time slots (15-minute intervals)
        current_time = start_datetime
        slots_created = 0

        while current_time < end_datetime:
            next_time = current_time + timedelta(minutes=15)

            # Check if slot already exists
            existing_slot = TimeSlot.query.filter_by(
                doctor_id=current_user.id,
                start_time=current_time
            ).first()

            if not existing_slot:
                time_slot = TimeSlot(
                    doctor_id=current_user.id,
                    start_time=current_time,
                    end_time=next_time
                )
                db.session.add(time_slot)
                slots_created += 1

            current_time = next_time

        db.session.commit()
        flash(f'{slots_created} time slots created successfully!', 'success')
        return redirect(url_for('doctors.time_slots'))

    # Get existing time slots
    upcoming_slots = TimeSlot.query.filter_by(
        doctor_id=current_user.id
    ).filter(
        TimeSlot.start_time >= get_local_time()
    ).order_by(TimeSlot.start_time).all()

    # Group time slots by date for better display
    grouped_slots = {}
    for slot in upcoming_slots:
        date_str = slot.start_time.strftime('%Y-%m-%d')
        if date_str not in grouped_slots:
            grouped_slots[date_str] = []
        grouped_slots[date_str].append(slot)

    return render_template(
        'doctors/time_slots.html',
        title='Manage Time Slots',
        form=form,
        bulk_form=bulk_form,
        upcoming_slots=upcoming_slots,
        grouped_slots=grouped_slots,
        format_time_slot=format_time_slot
    )

@doctors_bp.route('/bulk-time-slots', methods=['POST'])
@login_required
@doctor_required
def bulk_time_slots():
    """Create bulk time slots for multiple days."""
    form = BulkTimeSlotForm()

    if form.validate_on_submit():
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
            return redirect(url_for('doctors.time_slots'))

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
                        doctor_id=current_user.id,
                        start_time=current_time
                    ).first()

                    if not existing_slot:
                        time_slot = TimeSlot(
                            doctor_id=current_user.id,
                            start_time=current_time,
                            end_time=next_time
                        )
                        db.session.add(time_slot)
                        slots_created += 1

                    current_time = next_time

            # Move to next day
            current_date += timedelta(days=1)

        db.session.commit()
        flash(f'{slots_created} time slots created successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('doctors.time_slots'))

@doctors_bp.route('/delete-time-slot/<int:slot_id>', methods=['POST'])
@login_required
@doctor_required
def delete_time_slot(slot_id):
    """Delete a time slot."""
    # Get the time slot
    time_slot = TimeSlot.query.filter_by(
        id=slot_id,
        doctor_id=current_user.id
    ).first_or_404()

    # Check if the time slot is booked
    if time_slot.is_booked:
        flash('Cannot delete a booked time slot.', 'danger')
        return redirect(url_for('doctors.time_slots'))

    # Delete the time slot
    db.session.delete(time_slot)
    db.session.commit()

    flash('Time slot deleted successfully!', 'success')
    return redirect(url_for('doctors.time_slots'))

@doctors_bp.route('/delete-day-slots/<string:date_str>', methods=['POST'])
@login_required
@doctor_required
def delete_day_slots(date_str):
    """Delete all time slots for a specific day."""
    try:
        # Parse the date string
        year, month, day = map(int, date_str.split('-'))
        date = datetime(year, month, day).date()

        # Get all time slots for this day
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = datetime.combine(date, datetime.max.time())

        # Find all unbooked time slots for this day
        time_slots = TimeSlot.query.filter(
            TimeSlot.doctor_id == current_user.id,
            TimeSlot.start_time >= start_datetime,
            TimeSlot.start_time < end_datetime,
            TimeSlot.is_booked == False
        ).all()

        # Delete the time slots
        slots_deleted = 0
        for slot in time_slots:
            db.session.delete(slot)
            slots_deleted += 1

        db.session.commit()

        flash(f'{slots_deleted} time slots deleted successfully!', 'success')
    except ValueError:
        flash('Invalid date format.', 'danger')

    return redirect(url_for('doctors.time_slots'))

@doctors_bp.route('/notifications')
@login_required
@doctor_required
def notifications():
    """View all notifications."""
    # Get all notifications
    notifications = Notification.query.filter_by(
        recipient_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()

    # Mark notifications as read
    unread_count = 0
    for notification in notifications:
        if not notification.is_read:
            notification.is_read = True
            unread_count += 1

    if unread_count > 0:
        db.session.commit()
        flash(f'Marked {unread_count} notifications as read', 'info')

    return render_template(
        'doctors/notifications.html',
        title='My Notifications',
        notifications=notifications
    )

@doctors_bp.route('/api/predict-skin-disease/<int:upload_id>')
@login_required
@doctor_required
def predict_skin_disease_api(upload_id):
    """API endpoint to predict skin disease from an uploaded image."""
    try:
        # Get the image upload
        current_app.logger.info(f"Processing prediction request for upload ID: {upload_id}")
        upload = ImageUpload.query.filter_by(
            id=upload_id,
            doctor_id=current_user.id
        ).first_or_404()

        current_app.logger.info(f"Found upload with image path: {upload.image_path}")

        # Ensure the image is 300x300 for ML model
        image_path = os.path.join(current_app.static_folder, upload.image_path)
        current_app.logger.info(f"Full image path: {image_path}")

        if not os.path.exists(image_path):
            current_app.logger.error(f"Image file not found at: {image_path}")
            return jsonify({"error": f"Image file not found: {upload.image_path}"})

        # Resize the image
        resize_success = resize_image_to_300x300(image_path)
        if not resize_success:
            current_app.logger.warning(f"Failed to resize image to 300x300: {image_path}")
        else:
            current_app.logger.info(f"Successfully resized image to 300x300: {image_path}")

        # Make prediction
        current_app.logger.info(f"Making prediction for image: {upload.image_path}")
        prediction_results = predict_skin_disease(upload.image_path)

        # Log detailed prediction results
        if 'error' in prediction_results:
            current_app.logger.error(f"Prediction error: {prediction_results['error']}")
            if 'model_status' in prediction_results:
                current_app.logger.error(f"Model status: {prediction_results['model_status']}")
        else:
            current_app.logger.info(f"Prediction successful!")
            current_app.logger.info(f"Top prediction: {prediction_results['top_prediction']['class']} with {prediction_results['top_prediction']['percentage']} probability")
            # Log first 3 predictions
            top_three = []
            for p in prediction_results['all_predictions'][:3]:
                top_three.append(f"{p['class']}: {p['percentage']}")
            current_app.logger.info(f"Top 3 predictions: {top_three}")

        return jsonify(prediction_results)
    except Exception as e:
        import traceback
        current_app.logger.error(f"Error in prediction API: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"})
