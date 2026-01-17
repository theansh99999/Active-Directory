#!/usr/bin/env python
"""Test to verify grant_admin_rights is being saved correctly"""
from app import app, db
from models import User, Group

with app.app_context():
    print("=" * 70)
    print("CHECKING GROUP ADMIN RIGHTS SETTINGS")
    print("=" * 70)
    
    # Get all groups
    all_groups = Group.query.all()
    print(f"\nTotal groups in database: {len(all_groups)}")
    
    for group in all_groups:
        print(f"\nGroup: '{group.name}'")
        print(f"  ID: {group.id}")
        print(f"  Permissions: {group.permissions}")
        print(f"  grant_admin_rights: {group.grant_admin_rights}")
        print(f"  Members: {len(group.members)}")
        
        for member in group.members:
            is_admin = member.is_admin()
            print(f"    - {member.username}: is_admin()={is_admin}")
    
    # Check amit specifically
    print("\n" + "-" * 70)
    amit = User.query.filter_by(username='amit').first()
    if amit:
        print(f"\nAmit's Status:")
        print(f"  Role: {amit.role}")
        print(f"  is_admin(): {amit.is_admin()}")
        print(f"  Groups: {amit.groups}")
        for g in amit.groups:
            print(f"    - {g.name}: grant_admin_rights={g.grant_admin_rights}")
    
    print("\n" + "=" * 70)
