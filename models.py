"""
Database models for the Active Directory Clone application.
"""
from datetime import datetime, timedelta,timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import re

db = SQLAlchemy()

# Association table for many-to-many relationship between users and groups with roles
group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('role', db.String(20), nullable=False, default='User'),  # User or Admin within group
    db.Column('added_at', db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
)

class User(UserMixin, db.Model):
    """User model for authentication and user management."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='User')  # Admin or User
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    ou_id = db.Column(db.Integer, db.ForeignKey('organizational_unit.id'), nullable=True)
    
    # Relationships
    groups = db.relationship('Group', secondary=group_members, lazy='subquery',
                           backref=db.backref('members', lazy=True))
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set password hash after validation."""
        if not self.validate_password_strength(password):
            raise ValueError("Password does not meet security requirements")
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash."""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password meets security requirements."""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True
    
    def is_locked(self):
        """Check if account is currently locked."""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False
    
    def lock_account(self):
        """Lock account for specified duration."""
        from config import Config
        self.locked_until = datetime.utcnow() + Config.ACCOUNT_LOCKOUT_DURATION
        self.failed_attempts = 0
    
    def unlock_account(self):
        """Unlock account and reset failed attempts."""
        self.locked_until = None
        self.failed_attempts = 0
    
    def increment_failed_attempts(self):
        """Increment failed login attempts."""
        from config import Config
        self.failed_attempts += 1
        if self.failed_attempts >= Config.MAX_FAILED_ATTEMPTS:
            self.lock_account()
    
    def is_admin(self):
        """Check if user is admin (by role or group membership)."""
        # Check direct admin role
        if self.role == 'Admin':
            return True
        # Check if member of any admin-granting group
        admin_groups = [g for g in self.groups if g.grant_admin_rights]
        return len(admin_groups) > 0
    
    def has_read_write_permission(self):
        """Check if user has read-write permission (through role or group membership)."""
        # Admins always have read-write
        if self.is_admin():
            return True
        # Check if member of any read-write permission group (legacy) or admin group
        read_write_groups = [g for g in self.groups if g.permissions in ['read-write', 'admin']]
        return len(read_write_groups) > 0
    
    def __repr__(self):
        return f'<User {self.username}>'

class Group(db.Model):
    """Group model for organizing users and managing permissions."""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    permissions = db.Column(db.String(50), nullable=False, default='user')  # user, admin
    grant_admin_rights = db.Column(db.Boolean, default=False, nullable=False)  # Whether members get admin role
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ou_id = db.Column(db.Integer, db.ForeignKey('organizational_unit.id'), nullable=True)
    
    def get_member_role(self, user):
        """Get effective role for a user in this group (considering admin rights)."""
        if self.grant_admin_rights and user in self.members:
            return 'Admin'
        return user.role
    
    def __repr__(self):
        return f'<Group {self.name}>'

class OrganizationalUnit(db.Model):
    """Organizational Unit model for hierarchical structure."""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('organizational_unit.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('name', 'parent_id', name='uq_ou_name_parent'),
    )
    
    # Self-referential relationship for hierarchy
    parent = db.relationship('OrganizationalUnit', remote_side=[id], backref='children')
    computers = db.relationship('Computer', backref='organizational_unit', lazy=True)
    users = db.relationship('User', backref='organizational_unit', lazy=True)
    groups = db.relationship('Group', backref='organizational_unit', lazy=True)
    
    def get_full_path(self):
        """Get full hierarchical path of the OU."""
        path = [self.name]
        current = self.parent
        while current:
            path.append(current.name)
            current = current.parent
        return ' > '.join(reversed(path))
    
    def __repr__(self):
        return f'<OU {self.name}>'

class Computer(db.Model):
    """Computer model for managing computer accounts."""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='OFF')  # ON, OFF, RESTART
    operating_system = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(15), nullable=True)
    ou_id = db.Column(db.Integer, db.ForeignKey('organizational_unit.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Computer {self.name}>'

class AuditLog(db.Model):
    """Audit log model for tracking system actions."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = db.Column(db.String(15), nullable=True)
    
    @staticmethod
    def log_action(user_id, action, target, details=None, ip_address=None):
        """Create a new audit log entry."""
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            target=target,
            details=details,
            ip_address=ip_address
        )
        db.session.add(log_entry)
        db.session.commit()
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.target}>'