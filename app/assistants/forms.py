"""
Assistant forms for Easy Clinic Portal.
"""
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, DateTimeField, SelectMultipleField
from wtforms.validators import DataRequired
from app.models.user import User, Role
from app.models.appointment import AppointmentStatus

class RescheduleAppointmentForm(FlaskForm):
    """Form for rescheduling appointments."""
    doctor = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    time_slot = SelectField('Time Slot', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[
        (AppointmentStatus.SCHEDULED.value, 'Scheduled'),
        (AppointmentStatus.CANCELLED.value, 'Cancelled'),
        (AppointmentStatus.RESCHEDULED.value, 'Rescheduled')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Appointment')

    def __init__(self, *args, **kwargs):
        super(RescheduleAppointmentForm, self).__init__(*args, **kwargs)
        # Populate doctor choices
        doctors = User.query.filter_by(role=Role.DOCTOR).all()
        self.doctor.choices = [(d.id, d.name) for d in doctors]
        # Time slot choices will be populated via AJAX based on selected doctor

class DoctorTimeSlotForm(FlaskForm):
    """Form for creating time slots for doctors."""
    doctor = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    date = DateTimeField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    start_time = SelectField('Start Time', choices=[], validators=[DataRequired()])
    end_time = SelectField('End Time', choices=[], validators=[DataRequired()])
    submit = SubmitField('Create Time Slots')

    def __init__(self, *args, **kwargs):
        super(DoctorTimeSlotForm, self).__init__(*args, **kwargs)
        # Populate doctor choices
        doctors = User.query.filter_by(role=Role.DOCTOR).all()
        self.doctor.choices = [(d.id, d.name) for d in doctors]

        # Generate time choices (10:00 AM to 10:00 PM, 15-min intervals)
        time_choices = []
        for hour in range(10, 22):  # 10 AM to 10 PM
            for minute in [0, 15, 30, 45]:
                time_str = f"{hour:02d}:{minute:02d}"
                display_str = f"{hour:02d}:{minute:02d} {('AM' if hour < 12 else 'PM')}"
                time_choices.append((time_str, display_str))

        self.start_time.choices = time_choices
        self.end_time.choices = time_choices

class BulkDoctorTimeSlotForm(FlaskForm):
    """Form for creating bulk time slots for doctors."""
    doctor = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    start_date = DateTimeField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateTimeField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    days_of_week = SelectMultipleField('Days of Week', choices=[
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], validators=[DataRequired()])
    start_time = SelectField('Start Time', choices=[], validators=[DataRequired()])
    end_time = SelectField('End Time', choices=[], validators=[DataRequired()])
    submit = SubmitField('Create Bulk Time Slots')

    def __init__(self, *args, **kwargs):
        super(BulkDoctorTimeSlotForm, self).__init__(*args, **kwargs)
        # Populate doctor choices
        doctors = User.query.filter_by(role=Role.DOCTOR).all()
        self.doctor.choices = [(d.id, d.name) for d in doctors]

        # Generate time choices (10:00 AM to 10:00 PM, 15-min intervals)
        time_choices = []
        for hour in range(10, 22):  # 10 AM to 10 PM
            for minute in [0, 15, 30, 45]:
                time_str = f"{hour:02d}:{minute:02d}"
                display_str = f"{hour:02d}:{minute:02d} {('AM' if hour < 12 else 'PM')}"
                time_choices.append((time_str, display_str))

        self.start_time.choices = time_choices
        self.end_time.choices = time_choices
