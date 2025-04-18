"""
Patient forms for Easy Clinic Portal.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from app.models.user import User, Role
from app.models.appointment import AppointmentStatus

class ProfileForm(FlaskForm):
    """Form for patient profile information."""
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    address = StringField('Address', validators=[Optional(), Length(max=200)])
    medical_history = TextAreaField('Medical History', validators=[Optional()])
    allergies = TextAreaField('Allergies', validators=[Optional()])
    submit = SubmitField('Update Profile')

class AppointmentForm(FlaskForm):
    """Form for scheduling appointments."""
    doctor = SelectField('Select Doctor', coerce=int, validators=[DataRequired()])
    time_slot = SelectField('Select Time Slot', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('Reason for Visit', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Schedule Appointment')

    def __init__(self, *args, **kwargs):
        super(AppointmentForm, self).__init__(*args, **kwargs)
        # Populate doctor choices
        doctors = User.query.filter_by(role=Role.DOCTOR).all()
        self.doctor.choices = [(d.id, d.name) for d in doctors]
        # Initialize time_slot choices with an empty list
        # This will be populated via AJAX based on selected doctor
        self.time_slot.choices = []

class RescheduleAppointmentForm(FlaskForm):
    """Form for rescheduling appointments."""
    appointment_id = HiddenField('Appointment ID', validators=[DataRequired()])
    time_slot = SelectField('Select New Time Slot', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('Reason for Rescheduling (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Reschedule Appointment')

    def __init__(self, *args, **kwargs):
        super(RescheduleAppointmentForm, self).__init__(*args, **kwargs)
        # Time slot choices will be populated via AJAX
        self.time_slot.choices = []

class CancelAppointmentForm(FlaskForm):
    """Form for cancelling appointments."""
    appointment_id = HiddenField('Appointment ID', validators=[DataRequired()])
    reason = TextAreaField('Reason for Cancellation (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Cancel Appointment')

class ImageUploadForm(FlaskForm):
    """Form for uploading symptom images."""
    doctor = SelectField('Select Doctor', coerce=int, validators=[DataRequired()])
    image = FileField('Upload Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    message = TextAreaField('Message (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Upload Image')

    def __init__(self, *args, **kwargs):
        super(ImageUploadForm, self).__init__(*args, **kwargs)
        # Populate doctor choices
        doctors = User.query.filter_by(role=Role.DOCTOR).all()
        self.doctor.choices = [(d.id, d.name) for d in doctors]
