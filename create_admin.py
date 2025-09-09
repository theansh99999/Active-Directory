from app import app, db
from models import User

with app.app_context():
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',       # <- yaha value add karo
            last_name='User',         # <- yaha value add karo
            role='Admin',
            is_active=True
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")
