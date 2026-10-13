import sys
import os

# Add the project root to the sys.path so we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.data.database import SessionLocal, engine, Base
from backend.data.models import User
from backend.api.routers.auth_router import get_password_hash

def create_superadmin(username, password, name):
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"User '{username}' already exists. Updating password and role to admin...")
            existing_user.hashed_password = get_password_hash(password)
            existing_user.role = "admin"
            existing_user.name = name
        else:
            print(f"Creating new superadmin '{username}'...")
            new_admin = User(
                username=username,
                hashed_password=get_password_hash(password),
                role="admin",
                name=name,
                organisation="System Administration",
                station="HQ",
                is_active=True
            )
            db.add(new_admin)
            
        db.commit()
        print("Superadmin account successfully created/updated!")
        print(f"Username: {username}")
        print(f"Password: {password}")
        
    except Exception as e:
        print(f"Error creating superadmin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("--- Aviation Weather System Superadmin Setup ---")
    admin_id = "ADM-001"
    admin_name = "ashan"
    admin_pwd = "password123"
    
    if len(admin_pwd) < 6:
        print("Password too short. Must be at least 6 characters.")
    elif not admin_id or not admin_name:
        print("ID and Name cannot be empty.")
    else:
        create_superadmin(admin_id, admin_pwd, admin_name)
