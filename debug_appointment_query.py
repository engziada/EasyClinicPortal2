from app import db, create_app
from app.models.appointment import Appointment, TimeSlot, AppointmentStatus
from app.models.user import User
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print('--- Testing Appointment Queries ---')
    
    # Get all appointments
    all_appointments = Appointment.query.all()
    print(f'Total appointments in database: {len(all_appointments)}')
    
    # Test the dashboard query
    dashboard_appointments = Appointment.query.filter_by(
        patient_id=5,  # Patient 1's ID
        status=AppointmentStatus.SCHEDULED
    ).join(TimeSlot).filter(
        TimeSlot.start_time >= datetime.utcnow()
    ).order_by(TimeSlot.start_time).all()
    
    print(f'Dashboard query results (SCHEDULED only): {len(dashboard_appointments)}')
    
    # Test with both SCHEDULED and RESCHEDULED
    dashboard_appointments_both = Appointment.query.filter(
        Appointment.patient_id == 5,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED])
    ).join(TimeSlot).filter(
        TimeSlot.start_time >= datetime.utcnow()
    ).order_by(TimeSlot.start_time).all()
    
    print(f'Dashboard query results (SCHEDULED and RESCHEDULED): {len(dashboard_appointments_both)}')
    
    # Print details of appointments found
    for a in dashboard_appointments_both:
        patient = User.query.get(a.patient_id)
        doctor = User.query.get(a.doctor_id)
        time_slot = TimeSlot.query.get(a.time_slot_id)
        
        print(f'ID: {a.id}, Patient: {patient.name}, Doctor: {doctor.name}, Status: {a.status.value}')
        print(f'    Time Slot: {time_slot.start_time.strftime("%Y-%m-%d %H:%M")} - {time_slot.end_time.strftime("%Y-%m-%d %H:%M")}')
