"""
User models for Easy Clinic Portal.
"""
from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class Role(Enum):
    """User roles in the system."""
    PATIENT = 'patient'
    DOCTOR = 'doctor'
    ASSISTANT = 'assistant'
    ADMIN = 'admin'
    SUPERADMIN = 'superadmin'

class User(db.Model, UserMixin):
    """Base user model for all user types."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient_profile = db.relationship('PatientProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    doctor_profile = db.relationship('DoctorProfile', backref='user', uselist=False, cascade='all, delete-orphan')

    # Appointments
    doctor_appointments = db.relationship('Appointment', foreign_keys='Appointment.doctor_id', backref='doctor')
    patient_appointments = db.relationship('Appointment', foreign_keys='Appointment.patient_id', backref='patient')

    # Image uploads
    doctor_image_uploads = db.relationship('ImageUpload', foreign_keys='ImageUpload.doctor_id', backref='doctor')
    patient_image_uploads = db.relationship('ImageUpload', foreign_keys='ImageUpload.patient_id', backref='patient')

    # Diagnostic records
    doctor_diagnostic_records = db.relationship('DiagnosticRecord', foreign_keys='DiagnosticRecord.doctor_id', backref='doctor')
    patient_diagnostic_records = db.relationship('DiagnosticRecord', foreign_keys='DiagnosticRecord.patient_id', backref='patient')

    # Notifications
    notifications = db.relationship('Notification', foreign_keys='Notification.recipient_id', backref='recipient')

    # Time slots (for doctors)
    time_slots = db.relationship('TimeSlot', backref='doctor')

    @property
    def password(self):
        """Prevent password from being accessed."""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """Set password to a hashed password."""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Check if password matches the hashed password."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user is an admin or superadmin."""
        return self.role in [Role.ADMIN, Role.SUPERADMIN]

    def is_doctor(self):
        """Check if user is a doctor."""
        return self.role == Role.DOCTOR

    def is_patient(self):
        """Check if user is a patient."""
        return self.role == Role.PATIENT

    def is_assistant(self):
        """Check if user is an assistant."""
        return self.role == Role.ASSISTANT

    def is_superadmin(self):
        """Check if user is a superadmin."""
        return self.role == Role.SUPERADMIN

    def get_id(self):
        """Return the user ID as a unicode string."""
        return str(self.id)

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True

    def is_anonymous(self):
        """Return False as anonymous users aren't supported."""
        return False

    @property
    def active(self):
        """Return True if this is an active user."""
        return self.is_active

    def __repr__(self):
        return f'<User {self.name}, {self.role.value}>'

class PatientProfile(db.Model):
    """Profile information specific to patients."""
    __tablename__ = 'patient_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    medical_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PatientProfile for User {self.user_id}>'

class DoctorProfile(db.Model):
    """Profile information specific to doctors."""
    __tablename__ = 'doctor_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialization = db.Column(db.String(100))
    degree = db.Column(db.String(100))
    license_number = db.Column(db.String(50))
    bio = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<DoctorProfile for User {self.user_id}>'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.query.get(int(user_id))
