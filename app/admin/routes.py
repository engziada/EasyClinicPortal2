"""
Admin routes for Easy Clinic Portal.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.admin.forms import CreateUserForm, DoctorTimeSlotForm, BulkDoctorTimeSlotForm
from app.models.user import User, Role, DoctorProfile
from app.models.appointment import Appointment, TimeSlot
from app.models.image import ImageUpload
from app.models.notification import Notification, NotificationType
from app.utils.helpers import admin_required, format_time_slot

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard."""
    # Get user counts
    doctor_count = User.query.filter_by(role=Role.DOCTOR).count()
    patient_count = User.query.filter_by(role=Role.PATIENT).count()
    assistant_count = User.query.filter_by(role=Role.ASSISTANT).count()

    # Get appointment count
    appointment_count = Appointment.query.count()

    # Get image upload count
    image_count = ImageUpload.query.count()

    return render_template(
        'admin/dashboard.html',
        title='Admin Dashboard',
        doctor_count=doctor_count,
        patient_count=patient_count,
        assistant_count=assistant_count,
        appointment_count=appointment_count,
        image_count=image_count
    )

@admin_bp.route('/create-user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create a new user (doctor or assistant)."""
    form = CreateUserForm()

    if form.validate_on_submit():
        # Create new user
        role = Role.DOCTOR if form.role.data == 'doctor' else Role.ASSISTANT

        user = User(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,
            role=role
        )

        db.session.add(user)

        # Create profile for doctors
        if role == Role.DOCTOR:
            profile = DoctorProfile(
                user=user,
                specialization=form.specialization.data,
                degree=form.degree.data,
                license_number=form.license_number.data,
                is_admin=form.is_admin.data
            )
            db.session.add(profile)

        db.session.commit()

        flash(f'{role.value.capitalize()} created successfully!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/create_user.html', title='Create User', form=form)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """View all users."""
    # Get all users
    doctors = User.query.filter_by(role=Role.DOCTOR).all()
    patients = User.query.filter_by(role=Role.PATIENT).all()
    assistants = User.query.filter_by(role=Role.ASSISTANT).all()

    return render_template(
        'admin/users.html',
        title='All Users',
        doctors=doctors,
        patients=patients,
        assistants=assistants
    )

@admin_bp.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit a user."""
    # Get the user
    user = User.query.get_or_404(user_id)

    # Prevent editing superadmin
    if user.is_superadmin():
        flash('Cannot edit superadmin user.', 'danger')
        return redirect(url_for('admin.users'))

    form = CreateUserForm()

    if form.validate_on_submit():
        # Update user
        user.name = form.name.data

        # Only update password if provided
        if form.password.data:
            user.password = form.password.data

        # Update role if changed and not superadmin
        if not user.is_superadmin():
            new_role = Role.DOCTOR if form.role.data == 'doctor' else Role.ASSISTANT

            # Handle role change
            if user.role != new_role:
                user.role = new_role

                # Create or delete profiles as needed
                if new_role == Role.DOCTOR and not user.doctor_profile:
                    profile = DoctorProfile(
                        user=user,
                        specialization=form.specialization.data,
                        degree=form.degree.data,
                        license_number=form.license_number.data,
                        is_admin=form.is_admin.data
                    )
                    db.session.add(profile)
                elif new_role == Role.ASSISTANT and user.doctor_profile:
                    db.session.delete(user.doctor_profile)

            # Update doctor profile if role is doctor
            if new_role == Role.DOCTOR and user.doctor_profile:
                user.doctor_profile.specialization = form.specialization.data
                user.doctor_profile.degree = form.degree.data
                user.doctor_profile.license_number = form.license_number.data
                user.doctor_profile.is_admin = form.is_admin.data

        db.session.commit()

        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))

    # Pre-populate form with existing data
    if request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        form.role.data = 'doctor' if user.is_doctor() else 'assistant'

        if user.is_doctor() and user.doctor_profile:
            form.is_admin.data = user.doctor_profile.is_admin
            form.specialization.data = user.doctor_profile.specialization
            form.degree.data = user.doctor_profile.degree
            form.license_number.data = user.doctor_profile.license_number

    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user."""
    # Get the user
    user = User.query.get_or_404(user_id)

    # Prevent deleting superadmin or self
    if user.is_superadmin() or user.id == current_user.id:
        flash('Cannot delete this user.', 'danger')
        return redirect(url_for('admin.users'))

    # Delete user
    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/appointments')
@login_required
@admin_required
def appointments():
    """View all appointments."""
    # Get all appointments
    appointments = Appointment.query.all()

    return render_template(
        'admin/appointments.html',
        title='All Appointments',
        appointments=appointments
    )

@admin_bp.route('/uploads')
@login_required
@admin_required
def uploads():
    """View all image uploads."""
    # Get all image uploads
    uploads = ImageUpload.query.all()

    return render_template(
        'admin/uploads.html',
        title='All Uploads',
        uploads=uploads
    )

@admin_bp.route('/doctor-availability', methods=['GET', 'POST'])
@login_required
@admin_required
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
            return redirect(url_for('admin.doctor_availability'))

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
            message=f'Admin {current_user.name} has created {slots_created} new time slots for you on {date.strftime("%Y-%m-%d")}'
        )
        db.session.add(notification)
        db.session.commit()

        flash(f'{slots_created} time slots created successfully for {User.query.get(doctor_id).name}!', 'success')
        return redirect(url_for('admin.doctor_availability'))

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
        'admin/doctor_availability.html',
        title='Doctor Availability',
        availability=availability,
        form=form,
        bulk_form=bulk_form,
        format_time_slot=format_time_slot
    )

@admin_bp.route('/bulk-time-slots', methods=['POST'])
@login_required
@admin_required
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
            return redirect(url_for('admin.doctor_availability'))

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
            message=f'Admin {current_user.name} has created {slots_created} new time slots for you between {start_date.strftime("%Y-%m-%d")} and {end_date.strftime("%Y-%m-%d")}'
        )
        db.session.add(notification)
        db.session.commit()

        flash(f'{slots_created} time slots created successfully for {User.query.get(doctor_id).name}!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('admin.doctor_availability'))

@admin_bp.route('/delete-time-slot/<int:slot_id>', methods=['POST'])
@login_required
@admin_required
def delete_time_slot(slot_id):
    """Delete a time slot."""
    # Get the time slot
    time_slot = TimeSlot.query.get_or_404(slot_id)

    # Check if the time slot is booked
    if time_slot.is_booked:
        flash('Cannot delete a booked time slot.', 'danger')
        return redirect(url_for('admin.doctor_availability'))

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
        message=f'Admin {current_user.name} has deleted your time slot at {slot_time}'
    )
    db.session.add(notification)
    db.session.commit()

    flash('Time slot deleted successfully!', 'success')
    return redirect(url_for('admin.doctor_availability'))

@admin_bp.route('/delete-day-slots/<int:doctor_id>/<string:date_str>', methods=['POST'])
@login_required
@admin_required
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
                message=f'Admin {current_user.name} has deleted {slots_deleted} of your time slots on {date_str}'
            )
            db.session.add(notification)

        db.session.commit()

        flash(f'{slots_deleted} time slots deleted successfully!', 'success')
    except ValueError:
        flash('Invalid date format.', 'danger')

    return redirect(url_for('admin.doctor_availability'))

@admin_bp.route('/reset-timetable/<int:doctor_id>', methods=['POST'])
@login_required
@admin_required
def reset_timetable(doctor_id):
    """Reset the entire timetable for a doctor (delete all future unbooked slots)."""
    # Get the doctor
    doctor = User.query.get_or_404(doctor_id)

    # Find all future unbooked time slots for this doctor
    time_slots = TimeSlot.query.filter(
        TimeSlot.doctor_id == doctor_id,
        TimeSlot.start_time >= datetime.utcnow(),
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
            message=f'Admin {current_user.name} has reset your timetable, deleting {slots_deleted} future time slots'
        )
        db.session.add(notification)

    db.session.commit()

    flash(f'Timetable reset successfully! {slots_deleted} time slots deleted.', 'success')
    return redirect(url_for('admin.doctor_availability'))

@admin_bp.route('/toggle-user-status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Activate or deactivate a user."""
    # Only superadmin can toggle user status
    if not current_user.is_superadmin():
        flash('Only superadmin can activate or deactivate users.', 'danger')
        return redirect(url_for('admin.users'))

    # Get the user
    user = User.query.get_or_404(user_id)

    # Don't allow deactivating superadmin
    if user.is_superadmin():
        flash('Cannot deactivate superadmin user.', 'danger')
        return redirect(url_for('admin.users'))

    # Toggle active status
    if not hasattr(user, 'is_active'):
        # Add is_active column if it doesn't exist
        user.is_active = False
    else:
        user.is_active = not user.is_active

    db.session.commit()

    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.name} has been {status}.', 'success')

    # Redirect based on where the request came from
    referrer = request.referrer
    if referrer and 'doctor-availability' in referrer:
        return redirect(url_for('admin.doctor_availability'))
    else:
        return redirect(url_for('admin.users'))
