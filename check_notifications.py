from app import db, create_app
from app.models.notification import Notification
from app.models.user import User, Role

app = create_app()

with app.app_context():
    # Find assistant users
    assistants = User.query.filter_by(role=Role.ASSISTANT).all()
    
    if assistants:
        print(f"Found {len(assistants)} assistants:")
        for assistant in assistants:
            print(f"Assistant ID: {assistant.id}, Name: {assistant.name}")
            
            # Get all notifications for this assistant
            all_notifications = Notification.query.filter_by(
                recipient_id=assistant.id
            ).order_by(Notification.created_at.desc()).all()
            
            # Get unread notifications for this assistant
            unread_notifications = Notification.query.filter_by(
                recipient_id=assistant.id,
                is_read=False
            ).order_by(Notification.created_at.desc()).all()
            
            print(f"  Total notifications: {len(all_notifications)}")
            print(f"  Unread notifications: {len(unread_notifications)}")
            
            # Print details of unread notifications
            if unread_notifications:
                print("  Unread notification details:")
                for notification in unread_notifications:
                    print(f"    - ID: {notification.id}, Type: {notification.type.value}, Is Read: {notification.is_read}")
                    print(f"      Message: {notification.message}")
            else:
                print("  No unread notifications found.")
    else:
        print("No assistant users found in the database.")
