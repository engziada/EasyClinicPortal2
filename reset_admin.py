"""
Script to reset the admin password.
"""
from app import create_app, db
from app.models.user import User, Role
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Find the admin user
    admin = User.query.filter_by(email='admin@easyclinic.com').first()
    
    if admin:
        print(f"Found admin user: {admin.name}, {admin.email}, Role: {admin.role}")
        
        # Reset the password
        admin.password_hash = generate_password_hash('admin123')
        db.session.commit()
        
        print("Admin password reset to 'admin123'")
    else:
        print("Admin user not found. Creating a new admin user...")
        
        # Create a new admin user
        admin = User(
            name='Super Admin',
            email='admin@easyclinic.com',
            password_hash=generate_password_hash('admin123'),
            role=Role.SUPERADMIN
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("New admin user created with password 'admin123'")
