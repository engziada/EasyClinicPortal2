"""
Notification models for Easy Clinic Portal.
"""
from datetime import datetime
from enum import Enum
from app import db

class NotificationType(Enum):
    """Type of notification."""
    APPOINTMENT = 'appointment'
    IMAGE_UPLOAD = 'image_upload'
    DIAGNOSTIC = 'diagnostic'
    SYSTEM = 'system'

class Notification(db.Model):
    """Notification model for in-app notifications."""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.Integer, nullable=True)  # ID of related entity (appointment, image, etc.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with sender
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}: To {self.recipient_id}, Type {self.type.value}>'
