"""
Database initialization script with demo data.
"""
from app import app
from models import db, User, Group, OrganizationalUnit, Computer, AuditLog
from datetime import datetime, timedelta
import random

def init_database():
    """Initialize database with demo data."""
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        print("Initializing database with demo data...")
        
        # Create Organizational Units
        root_ou = OrganizationalUnit(
            name="Corporate",
            description="Root organizational unit"
        )
        db.session.add(root_ou)
        db.session.commit()
        
        it_ou = OrganizationalUnit(
            name="IT Department",
            description="Information Technology Department",
            parent_id=root_ou.id
        )
        db.session.add(it_ou)
        
        hr_ou = OrganizationalUnit(
            name="HR Department",
            description="Human Resources Department",
            parent_id=root_ou.id
        )
        db.session.add(hr_ou)
        
        finance_ou = OrganizationalUnit(
            name="Finance Department",
            description="Finance and Accounting Department",
            parent_id=root_ou.id
        )
        db.session.add(finance_ou)
        
        db.session.commit()
        
        # Create Groups
        admin_group = Group(
            name="Domain Admins",
            description="Full administrative access to all systems",
            permissions="read-write"
        )
        db.session.add(admin_group)
        
        it_group = Group(
            name="IT Support",
            description="IT support staff with elevated privileges",
            permissions="read-write"
        )
        db.session.add(it_group)
        
        users_group = Group(
            name="Domain Users",
            description="Standard user group with basic access",
            permissions="read-only"
        )
        db.session.add(users_group)
        
        hr_group = Group(
            name="HR Staff",
            description="Human Resources staff group",
            permissions="read-write"
        )
        db.session.add(hr_group)
        
        db.session.commit()
        
        # Create Admin User with specified credentials
        admin_user = User(
            username="admin",
            email="admin@company.com",
            first_name="System",
            last_name="Administrator",
            role="Admin",
            is_active=True
        )
        admin_user.set_password("Admin123")
        db.session.add(admin_user)
        
        # Create Demo Users with valid passwords
        demo_users = [
            {
                "username": "jdoe",
                "email": "john.doe@company.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "User",
                "password": "User123!"
            },
            {
                "username": "asmith",
                "email": "alice.smith@company.com",
                "first_name": "Alice",
                "last_name": "Smith",
                "role": "User",
                "password": "User123!"
            },
            {
                "username": "bwilson",
                "email": "bob.wilson@company.com",
                "first_name": "Bob",
                "last_name": "Wilson",
                "role": "Admin",
                "password": "Admin123!"
            },
            {
                "username": "mjohnson",
                "email": "mary.johnson@company.com",
                "first_name": "Mary",
                "last_name": "Johnson",
                "role": "User",
                "password": "User123!"
            },
            {
                "username": "dlee",
                "email": "david.lee@company.com",
                "first_name": "David",
                "last_name": "Lee",
                "role": "User",
                "password": "User123!"
            }
        ]
        
        users_list = []
        for user_data in demo_users:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"],
                is_active=True
            )
            user.set_password(user_data["password"])
            db.session.add(user)
            users_list.append(user)
        
        db.session.commit()
        
        # Add users to groups
        admin_user.groups.append(admin_group)
        users_list[2].groups.append(admin_group)  # bwilson
        
        for user in users_list:
            user.groups.append(users_group)
            if user.username in ['jdoe', 'asmith']:
                user.groups.append(it_group)
            elif user.username == 'mjohnson':
                user.groups.append(hr_group)
        
        # Create Demo Computers
        demo_computers = [
            {
                "name": "WS-IT-001",
                "description": "IT Department Workstation 1",
                "operating_system": "Windows 11 Pro",
                "ip_address": "192.168.1.101",
                "status": "ON",
                "ou_id": it_ou.id
            },
            {
                "name": "WS-IT-002",
                "description": "IT Department Workstation 2",
                "operating_system": "Windows 11 Pro",
                "ip_address": "192.168.1.102",
                "status": "OFF",
                "ou_id": it_ou.id
            },
            {
                "name": "WS-HR-001",
                "description": "HR Department Workstation 1",
                "operating_system": "Windows 10 Pro",
                "ip_address": "192.168.1.201",
                "status": "ON",
                "ou_id": hr_ou.id
            },
            {
                "name": "WS-FIN-001",
                "description": "Finance Department Workstation 1",
                "operating_system": "Windows 11 Pro",
                "ip_address": "192.168.1.301",
                "status": "RESTART",
                "ou_id": finance_ou.id
            },
            {
                "name": "SRV-DC-001",
                "description": "Domain Controller Server",
                "operating_system": "Windows Server 2022",
                "ip_address": "192.168.1.10",
                "status": "ON",
                "ou_id": it_ou.id
            },
            {
                "name": "SRV-FILE-001",
                "description": "File Server",
                "operating_system": "Windows Server 2019",
                "ip_address": "192.168.1.20",
                "status": "ON",
                "ou_id": it_ou.id
            }
        ]
        
        for comp_data in demo_computers:
            computer = Computer(
                name=comp_data["name"],
                description=comp_data["description"],
                operating_system=comp_data["operating_system"],
                ip_address=comp_data["ip_address"],
                status=comp_data["status"],
                ou_id=comp_data["ou_id"],
                last_seen=datetime.utcnow() if comp_data["status"] == "ON" else None
            )
            db.session.add(computer)
        
        db.session.commit()
        
        # Create Demo Audit Logs
        demo_actions = [
            ("User Login", "User: admin", "Successful login from IP: 127.0.0.1"),
            ("User Created", "User: jdoe", "New user created with role: User"),
            ("Group Created", "Group: IT Support", "New group created with permissions: read-write"),
            ("Computer ON", "Computer: WS-IT-001", "Status changed from OFF to ON"),
            ("Password Reset", "User: asmith", "Admin reset password for user"),
            ("User Updated", "User: mjohnson", "User profile updated"),
            ("Computer RESTART", "Computer: WS-FIN-001", "Status changed from ON to RESTART"),
            ("Group Updated", "Group: Domain Users", "Group information updated"),
            ("OU Created", "OU: IT Department", "New organizational unit created"),
            ("User Login", "User: jdoe", "Successful login from IP: 192.168.1.101")
        ]
        
        for i, (action, target, details) in enumerate(demo_actions):
            log_time = datetime.utcnow() - timedelta(hours=random.randint(1, 72))
            audit_log = AuditLog(
                user_id=admin_user.id,
                action=action,
                target=target,
                details=details,
                timestamp=log_time,
                ip_address="127.0.0.1"
            )
            db.session.add(audit_log)
        
        db.session.commit()
        
        print("Database initialized successfully!")
        print("\nPrimary Admin Login Credentials:")
        print("Username: admin")
        print("Password: Admin123")
        print("\nAdditional Demo Credentials:")
        print("Admin: bwilson / Admin123!")
        print("User: jdoe / User123!")
        print("User: asmith / User123!")
        print("User: mjohnson / User123!")
        print("User: dlee / User123!")

if __name__ == '__main__':
    init_database()