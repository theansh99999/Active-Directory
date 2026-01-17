#!/usr/bin/env python3
"""
Database migration script to add grant_admin_rights column to group table.
Run this to add the new admin rights feature to existing database.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import inspect

def migrate_database():
    """Add grant_admin_rights column to group table if it doesn't exist."""
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*70)
        print("DATABASE MIGRATION: Adding Admin Rights Feature")
        print("="*70 + "\n")
        
        # Check if column exists
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('group')]
        
        if 'grant_admin_rights' in columns:
            print("✅ Column 'grant_admin_rights' already exists in group table")
            print("   No migration needed!\n")
            return
        
        print("⚙️  Adding 'grant_admin_rights' column to group table...\n")
        
        try:
            # Add column to existing table using SQLAlchemy
            from sqlalchemy import text
            with db.engine.begin() as connection:
                connection.execute(text(
                    'ALTER TABLE "group" ADD COLUMN grant_admin_rights BOOLEAN DEFAULT 0 NOT NULL'
                ))
            
            print("✅ Column added successfully!\n")
            print("Migration complete. You can now:")
            print("  1. Create groups with admin rights")
            print("  2. Add users to admin groups")
            print("  3. Users will inherit admin privileges\n")
            
        except Exception as e:
            print(f"❌ Error adding column: {e}\n")
            print("Alternative: Drop and recreate database")
            print("  python init_db.py")
            return False
        
        return True

def verify_migration():
    """Verify the migration was successful."""
    
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        columns = {c['name']: c['type'] for c in inspector.get_columns('group')}
        
        print("="*70)
        print("VERIFICATION")
        print("="*70 + "\n")
        
        if 'grant_admin_rights' in columns:
            print("✅ Migration successful!")
            print(f"   Column type: {columns['grant_admin_rights']}\n")
            
            print("Group table columns:")
            for col_name, col_type in sorted(columns.items()):
                print(f"  • {col_name}: {col_type}")
            
            return True
        else:
            print("❌ Migration failed - column not found\n")
            return False

if __name__ == '__main__':
    print("\nAdmin Rights Feature - Database Migration\n")
    
    # Run migration
    success = migrate_database()
    
    # Verify migration
    if success:
        verify_migration()
        print("\n" + "="*70)
        print("✅ DATABASE MIGRATION COMPLETE")
        print("="*70 + "\n")
        print("Next steps:")
        print("  1. Restart the Flask application")
        print("  2. Create a group with 'Grant Admin Rights' option")
        print("  3. Add users to the group")
        print("  4. Users will have admin access!\n")
    else:
        print("\n❌ Migration not performed\n")
