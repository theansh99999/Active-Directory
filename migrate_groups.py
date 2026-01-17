#!/usr/bin/env python
"""
Script to migrate existing database to support group member roles.
Run this after updating the codebase.
"""
from app import app
from models import db, User, Group

def migrate_database():
    """Migrate database schema for group member roles."""
    with app.app_context():
        print("Starting database migration...")
        
        # Create all tables (this will create the new group_members table with role column)
        db.create_all()
        
        print("✓ Database schema updated successfully!")
        print("✓ New 'group_members' table created with role support")
        print("\nYou can now use the enhanced group member management features:")
        print("  - Add users to groups with specific roles")
        print("  - Search for users when adding to groups")
        print("  - Remove users from groups")
        print("  - Track audit logs for all group changes")

if __name__ == '__main__':
    migrate_database()
    print("\nMigration complete!")
