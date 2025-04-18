from app import db, create_app
from app.models.appointment import Appointment, TimeSlot, AppointmentStatus
from app.models.user import User

app = create_app()

with app.app_context():
    print('--- Appointments ---')
    appointments = Appointment.query.all()
    for a in appointments:
        patient = User.query.get(a.patient_id)
        doctor = User.query.get(a.doctor_id)
        time_slot = TimeSlot.query.get(a.time_slot_id)
        print(f'ID: {a.id}, Patient: {patient.name} (ID: {a.patient_id}), Doctor: {doctor.name} (ID: {a.doctor_id}), Status: {a.status.value}')
        if time_slot:
            print(f'    Time Slot: {time_slot.start_time.strftime("%Y-%m-%d %H:%M")} - {time_slot.end_time.strftime("%Y-%m-%d %H:%M")}, Booked: {time_slot.is_booked}')
    
    print('\n--- Time Slots ---')
    time_slots = TimeSlot.query.all()
    for ts in time_slots:
        doctor = User.query.get(ts.doctor_id)
        print(f'ID: {ts.id}, Doctor: {doctor.name} (ID: {ts.doctor_id}), Start: {ts.start_time.strftime("%Y-%m-%d %H:%M")}, End: {ts.end_time.strftime("%Y-%m-%d %H:%M")}, Booked: {ts.is_booked}')
