# Easy Clinic Portal

A Flask-based web portal for a dermatology clinic, designed as a graduation project for students.

## Features

- **Multi-role system**: Supports Doctors, Patients, and Assistants
- **Appointment management**: Schedule, reschedule, and cancel appointments
- **Image uploads**: Patients can upload symptom images for doctors to review
- **Live inspection**: Doctors can conduct and document live patient inspections
- **Notifications**: In-app notifications for important events
- **Admin panel**: Manage users and system settings

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: Bootstrap 5, jQuery, Jinja2 templates
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF, WTForms

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/easy-clinic-portal.git
   cd easy-clinic-portal
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python run.py
   ```

5. Access the application at `http://localhost:5000`

## Default Credentials

The system is initialized with a superadmin account:

- **Email**: admin@easyclinic.com
- **Password**: admin123

## Project Structure

```
/app/
    /auth/          # Authentication routes and forms
    /patients/      # Patient-specific functionality
    /doctors/       # Doctor-specific functionality
    /assistants/    # Assistant-specific functionality
    /admin/         # Admin functionality
    /models/        # Database models
    /templates/     # Jinja2 templates
    /static/        # CSS, JS, and uploaded files
    /utils/         # Utility functions
config.py           # Configuration settings
run.py              # Application entry point
```

## User Roles

### Patients
- Register accounts
- Reserve appointments with doctors
- Upload symptom images
- View appointment history and diagnoses

### Doctors
- View and manage appointments
- Review uploaded images
- Conduct live inspections
- Create diagnostic records

### Assistants
- Manage appointments
- View doctor availability
- Reschedule or cancel appointments

### Admin/SuperAdmin
- Create doctor and assistant accounts
- Manage all users
- View system statistics

## License

This project is for educational purposes only.

## Acknowledgements

- Flask and its extensions
- Bootstrap for the UI components
- Font Awesome for icons
