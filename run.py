"""
Entry point for Easy Clinic Portal.
"""
import threading
import time
from app import create_app, db
from app.utils.appointment_tasks import update_missed_appointments

app = create_app()

def background_task():
    """Run background tasks periodically."""
    with app.app_context():
        while True:
            # Update missed appointments
            update_missed_appointments()

            # Sleep for 5 minutes
            time.sleep(300)

if __name__ == '__main__':
    # Start background task in a separate thread
    bg_thread = threading.Thread(target=background_task, daemon=True)
    bg_thread.start()

    app.run(debug=True, port=5001)
