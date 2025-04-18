"""
Appointment models for Easy Clinic Portal.
"""
from datetime import datetime
from enum import Enum
from app import db

class AppointmentStatus(Enum):
    """Status of an appointment."""
    SCHEDULED = 'scheduled'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    RESCHEDULED = 'rescheduled'
    NO_SHOW = 'no_show'

class Appointment(db.Model):
    """Appointment model for scheduling patient-doctor meetings."""
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'), nullable=False)
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with TimeSlot
    time_slot = db.relationship('TimeSlot', backref='appointment', uselist=False)

    def __repr__(self):
        return f'<Appointment {self.id}: Patient {self.patient_id} with Doctor {self.doctor_id}>'

class TimeSlot(db.Model):
    """Time slot model for doctor availability."""
    __tablename__ = 'time_slots'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TimeSlot {self.id}: Doctor {self.doctor_id}, {self.start_time.strftime("%Y-%m-%d %H:%M")}>'
