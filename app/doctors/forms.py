"""
Doctor forms for Easy Clinic Portal.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, SelectField, SelectMultipleField, DateTimeField
from wtforms.validators import DataRequired, Length, Optional

class DiagnosticForm(FlaskForm):
    """Form for diagnostic records."""
    notes = TextAreaField('Diagnostic Notes', validators=[DataRequired()])
    prescriptions = TextAreaField('Prescriptions', validators=[Optional()])
    recommendations = TextAreaField('Recommendations', validators=[Optional()])
    red_flag = BooleanField('Red Flag (Urgent Follow-up Required)')
    submit = SubmitField('Save Diagnostic Record')

class LiveInspectionForm(FlaskForm):
    """Form for live inspection during appointments."""
    notes = TextAreaField('Diagnostic Notes', validators=[DataRequired()])
    prescriptions = TextAreaField('Prescriptions', validators=[Optional()])
    recommendations = TextAreaField('Recommendations', validators=[Optional()])
    red_flag = BooleanField('Red Flag (Urgent Follow-up Required)')
    images = FileField('Upload Images', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ], render_kw={"multiple": True})
    submit = SubmitField('Complete Inspection')

class ProfileForm(FlaskForm):
    """Form for doctor profile information."""
    specialization = StringField('Specialization', validators=[Optional(), Length(max=100)])
    degree = StringField('Degree', validators=[Optional(), Length(max=100)])
    license_number = StringField('License Number', validators=[Optional(), Length(max=50)])
    bio = TextAreaField('Bio', validators=[Optional()])
    submit = SubmitField('Update Profile')

class TimeSlotForm(FlaskForm):
    """Form for creating time slots."""
    date = DateTimeField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    start_time = SelectField('Start Time', choices=[], validators=[DataRequired()])
    end_time = SelectField('End Time', choices=[], validators=[DataRequired()])
    submit = SubmitField('Create Time Slots')

    def __init__(self, *args, **kwargs):
        super(TimeSlotForm, self).__init__(*args, **kwargs)
        # Generate time choices (10:00 AM to 10:00 PM, 15-min intervals)
        time_choices = []
        for hour in range(10, 22):  # 10 AM to 10 PM
            for minute in [0, 15, 30, 45]:
                time_str = f"{hour:02d}:{minute:02d}"
                display_str = f"{hour:02d}:{minute:02d} {('AM' if hour < 12 else 'PM')}"
                time_choices.append((time_str, display_str))

        self.start_time.choices = time_choices
        self.end_time.choices = time_choices

class BulkTimeSlotForm(FlaskForm):
    """Form for creating bulk time slots for multiple days."""
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
        super(BulkTimeSlotForm, self).__init__(*args, **kwargs)
        # Generate time choices (10:00 AM to 10:00 PM, 15-min intervals)
        time_choices = []
        for hour in range(10, 22):  # 10 AM to 10 PM
            for minute in [0, 15, 30, 45]:
                time_str = f"{hour:02d}:{minute:02d}"
                display_str = f"{hour:02d}:{minute:02d} {('AM' if hour < 12 else 'PM')}"
                time_choices.append((time_str, display_str))

        self.start_time.choices = time_choices
        self.end_time.choices = time_choices
