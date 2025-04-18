"""
Image upload models for Easy Clinic Portal.
"""
from datetime import datetime
from app import db

class ImageUpload(db.Model):
    """Image upload model for patient symptom images."""
    __tablename__ = 'image_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text)
    is_reviewed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with DiagnosticRecord
    diagnostic_record = db.relationship('DiagnosticRecord', backref='image_upload', uselist=False)
    
    def __repr__(self):
        return f'<ImageUpload {self.id}: Patient {self.patient_id} to Doctor {self.doctor_id}>'

class DiagnosticRecord(db.Model):
    """Diagnostic record model for doctor's diagnosis and prescriptions."""
    __tablename__ = 'diagnostic_records'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('image_uploads.id'), nullable=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    notes = db.Column(db.Text)
    prescriptions = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    red_flag = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with Appointment
    appointment = db.relationship('Appointment', backref='diagnostic_record', uselist=False)
    
    def __repr__(self):
        return f'<DiagnosticRecord {self.id}: Doctor {self.doctor_id} for Patient {self.patient_id}>'
