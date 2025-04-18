from app import db, create_app
from app.models.appointment import Appointment, TimeSlot, AppointmentStatus
from app.models.user import User
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print('--- Appointment Status Check ---')
    appointments = Appointment.query.all()
    for a in appointments:
        patient = User.query.get(a.patient_id)
        doctor = User.query.get(a.doctor_id)
        time_slot = TimeSlot.query.get(a.time_slot_id)
        
        print(f'ID: {a.id}, Patient: {patient.name}, Doctor: {doctor.name}, Status: {a.status.value}')
        print(f'    Time Slot: {time_slot.start_time.strftime("%Y-%m-%d %H:%M")} - {time_slot.end_time.strftime("%Y-%m-%d %H:%M")}')
        
        # Check if this would be considered an upcoming appointment
        is_future = time_slot.start_time >= datetime.utcnow()
        is_scheduled = a.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED]
        
        print(f'    Is Future: {is_future}, Is Scheduled/Rescheduled: {is_scheduled}')
        print(f'    Would show in upcoming: {is_future and is_scheduled}')
        
        # Check time difference
        time_diff = time_slot.start_time - datetime.utcnow()
        print(f'    Days until appointment: {time_diff.days}, Hours: {time_diff.seconds // 3600}')
        
    print('\n--- Current Time ---')
    print(f'Current UTC time: {datetime.utcnow()}')
