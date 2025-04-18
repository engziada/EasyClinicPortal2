"""
Admin forms for Easy Clinic Portal.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateTimeField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User, Role

class CreateUserForm(FlaskForm):
    """Form for creating new users."""
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('doctor', 'Doctor'), ('assistant', 'Assistant')])
    is_admin = BooleanField('Admin Privileges (Doctors only)')

    # Doctor-specific fields
    specialization = StringField('Specialization', validators=[Length(max=100)])
    degree = StringField('Degree', validators=[Length(max=100)])
    license_number = StringField('License Number', validators=[Length(max=50)])

    submit = SubmitField('Create User')

    def validate_email(self, email):
        """Validate that the email is not already registered."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

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
