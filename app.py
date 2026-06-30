"""
Main Flask application for Active Directory Clone.
"""
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from urllib.parse import urlparse as url_parse

from datetime import datetime
import os

from config import config
from models import db, User, Group, OrganizationalUnit, Computer, AuditLog
from forms import LoginForm, UserForm, PasswordResetForm, GroupForm, OrganizationalUnitForm, ComputerForm, AdminPasswordResetForm, AddUserToGroupForm
from auth import admin_required, login_required_with_message, get_client_ip, read_write_required

def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_CONFIG', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Ensure user groups are refreshed on each request to reflect current permissions
    @app.before_request
    def before_request():
        from flask_login import current_user
        if current_user.is_authenticated:
            try:
                # Expire the user object to force reload from database
                # This ensures group memberships and permissions are always current
                db.session.expire(current_user)
                # Also expire all related objects
                db.session.expire_all()
            except Exception:
                pass  # If refresh fails, continue with current user object
    
    return app

app = create_app()

from ou_controller import ou_bp
app.register_blueprint(ou_bp)

# Routes
@app.route('/')
def index():
    """Redirect to dashboard or login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        
        # Check if account is locked
        if user.is_locked():
            flash('Account is locked due to too many failed login attempts. Please try again later.', 'error')
            return redirect(url_for('login'))
        
        # Check if account is active
        if not user.is_active:
            flash('Account has been deactivated. Please contact an administrator.', 'error')
            return redirect(url_for('login'))
        
        # Verify password
        if not user.check_password(form.password.data):
            user.increment_failed_attempts()
            db.session.commit()
            flash('Invalid username or password', 'error')
            
            # Log failed login attempt
            AuditLog.log_action(
                user_id=user.id,
                action='Failed Login Attempt',
                target=f'User: {user.username}',
                details=f'Failed login from IP: {get_client_ip()}',
                ip_address=get_client_ip()
            )
            return redirect(url_for('login'))
        
        # Successful login
        user.failed_attempts = 0
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        
        # Log successful login
        AuditLog.log_action(
            user_id=user.id,
            action='User Login',
            target=f'User: {user.username}',
            details=f'Successful login from IP: {get_client_ip()}',
            ip_address=get_client_ip()
        )
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)

@app.route('/admin-password-reset', methods=['GET', 'POST'])
def admin_password_reset():
    """Admin password reset page accessible from login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = AdminPasswordResetForm()
    if form.validate_on_submit():
        # Find the admin user
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user is None:
            flash('Admin user not found.', 'error')
            return redirect(url_for('login'))
        
        # Update admin password
        admin_user.set_password(form.new_password.data)
        admin_user.unlock_account()  # Unlock account if it was locked
        db.session.commit()
        
        # Log the password reset action
        AuditLog.log_action(
            user_id=admin_user.id,
            action='Admin Password Reset',
            target=f'User: {admin_user.username}',
            details=f'Admin password reset from login page - IP: {get_client_ip()}',
            ip_address=get_client_ip()
        )
        
        flash('Admin password has been reset successfully. You can now log in with the new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('admin_password_reset.html', title='Reset Admin Password', form=form)

@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    # Log logout action
    AuditLog.log_action(
        user_id=current_user.id,
        action='User Logout',
        target=f'User: {current_user.username}',
        details=f'User logged out from IP: {get_client_ip()}',
        ip_address=get_client_ip()
    )
    
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required_with_message
def dashboard():
    """Main dashboard."""
    page = request.args.get('page', 1, type=int)
    
    # Get summary statistics
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_groups': Group.query.count(),
        'total_computers': Computer.query.count(),
        'computers_online': Computer.query.filter_by(status='ON').count(),
        'total_ous': OrganizationalUnit.query.count()
    }
    
    # Fetch paginated logs only for the current user
    logs_query = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.timestamp.desc())
    pagination = logs_query.paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
    
    return render_template('dashboard.html', title='Dashboard', stats=stats, 
                           recent_logs=pagination.items, pagination=pagination)

@app.route('/users')
@login_required_with_message
def users():
    """User management page."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.first_name.contains(search)) |
            (User.last_name.contains(search))
        )
    
    users_pagination = query.order_by(User.username).paginate(
        page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False
    )
    
    return render_template('users.html', title='User Management', 
                         users=users_pagination.items, pagination=users_pagination, search=search)

@app.route('/users/add', methods=['GET', 'POST'])
@admin_required
@read_write_required
def add_user():
    """Add new user."""
    form = UserForm()
    
    if request.method == 'GET' and 'ou_id' in request.args:
        try:
            form.ou_id.data = int(request.args.get('ou_id'))
        except ValueError:
            pass
            
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data,
            is_active=form.is_active.data,
            ou_id=form.ou_id.data if form.ou_id.data != 0 else None
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='User Created',
            target=f'User: {user.username}',
            details=f'New user created with role: {user.role}',
            ip_address=get_client_ip()
        )
        
        flash(f'User {user.username} has been created successfully.', 'success')
        return redirect(url_for('users'))
    
    return render_template('user_form.html', title='Add User', form=form, action='Add')

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
@read_write_required
def edit_user(id):
    """Edit existing user."""
    user = User.query.get_or_404(id)
    form = UserForm(original_user=user)
    
    # Pre-populate form on GET request
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.role.data = user.role
        form.is_active.data = user.is_active
        form.ou_id.data = user.ou_id or 0
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        user.ou_id = form.ou_id.data if form.ou_id.data != 0 else None
        
        if form.password.data and form.password.data.strip():
            try:
                user.set_password(form.password.data)
            except ValueError:
                flash('Password does not meet security requirements.', 'error')
                return render_template('user_form.html', title='Edit User', form=form, action='Edit', user=user)
        
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='User Updated',
            target=f'User: {user.username}',
            details=f'User profile updated',
            ip_address=get_client_ip()
        )
        
        flash(f'User {user.username} has been updated successfully.', 'success')
        return redirect(url_for('users'))
    
    return render_template('user_form.html', title='Edit User', form=form, action='Edit', user=user)

@app.route('/users/delete/<int:id>', methods=['POST'])
@admin_required
@read_write_required
def delete_user(id):
    """Delete user."""
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    # Log action
    AuditLog.log_action(
        user_id=current_user.id,
        action='User Deleted',
        target=f'User: {username}',
        details=f'User account deleted',
        ip_address=get_client_ip()
    )
    
    flash(f'User {username} has been deleted successfully.', 'success')
    return redirect(url_for('users'))

@app.route('/users/reset-password/<int:id>', methods=['GET', 'POST'])
@admin_required
def reset_password(id):
    """Reset user password."""
    user = User.query.get_or_404(id)
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        user.unlock_account()  # Unlock account if it was locked
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='Password Reset',
            target=f'User: {user.username}',
            details=f'Admin reset password for user',
            ip_address=get_client_ip()
        )
        
        flash(f'Password has been reset for user {user.username}.', 'success')
        return redirect(url_for('users'))
    
    return render_template('password_reset.html', title='Reset Password', form=form, user=user)

@app.route('/groups')
@login_required_with_message
def groups():
    """Group management page."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Group.query
    if search:
        query = query.filter(Group.name.contains(search))
    
    groups_pagination = query.order_by(Group.name).paginate(
        page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False
    )
    
    return render_template('groups.html', title='Group Management',
                         groups=groups_pagination.items, pagination=groups_pagination, search=search)

@app.route('/groups/add', methods=['GET', 'POST'])
@admin_required
@read_write_required
def add_group():
    """Add new group."""
    form = GroupForm()
    
    if request.method == 'GET' and 'ou_id' in request.args:
        try:
            form.ou_id.data = int(request.args.get('ou_id'))
        except ValueError:
            pass
            
    if form.validate_on_submit():
        group = Group(
            name=form.name.data,
            description=form.description.data,
            permissions=form.permissions.data,
            grant_admin_rights=(form.permissions.data == 'admin'),
            ou_id=form.ou_id.data if form.ou_id.data != 0 else None
        )
        
        db.session.add(group)
        db.session.commit()
        
        # Add selected users to the group
        if form.users.data:
            for user_id in form.users.data:
                user = User.query.get(user_id)
                if user:
                    group.members.append(user)
            db.session.commit()
            
            # Log each user addition
            for user_id in form.users.data:
                user = User.query.get(user_id)
                if user:
                    AuditLog.log_action(
                        user_id=current_user.id,
                        action='User Added to Group',
                        target=f'Group: {group.name}',
                        details=f'User {user.username} added during group creation. Will inherit: {group.permissions} permissions{"+ Admin rights" if group.grant_admin_rights else ""}',
                        ip_address=get_client_ip()
                    )
        
        # Log group creation
        AuditLog.log_action(
            user_id=current_user.id,
            action='Group Created',
            target=f'Group: {group.name}',
            details=f'New group created with permissions: {group.permissions}. Admin rights: {"Yes" if group.grant_admin_rights else "No"}. Users added: {len(form.users.data) if form.users.data else 0}',
            ip_address=get_client_ip()
        )
        
        flash(f'Group {group.name} has been created successfully.', 'success')
        return redirect(url_for('groups'))
    
    return render_template('group_form.html', title='Add Group', form=form, action='Add')

@app.route('/groups/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
@read_write_required
def edit_group(id):
    """Edit existing group."""
    group = Group.query.get_or_404(id)
    form = GroupForm(original_group=group, obj=group)
    
    if request.method == 'GET':
        form.ou_id.data = group.ou_id or 0
    
    if form.validate_on_submit():
        group.name = form.name.data
        group.description = form.description.data
        group.permissions = form.permissions.data
        group.grant_admin_rights = (form.permissions.data == 'admin')
        group.ou_id = form.ou_id.data if form.ou_id.data != 0 else None
        
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='Group Updated',
            target=f'Group: {group.name}',
            details=f'Group information updated. Admin rights: {"Yes" if group.grant_admin_rights else "No"}',
            ip_address=get_client_ip()
        )
        
        flash(f'Group {group.name} has been updated successfully.', 'success')
        return redirect(url_for('groups'))
    
    return render_template('group_form.html', title='Edit Group', form=form, action='Edit', group=group)

@app.route('/groups/delete/<int:id>', methods=['POST'])
@admin_required
@read_write_required
def delete_group(id):
    """Delete group."""
    group = Group.query.get_or_404(id)
    group_name = group.name
    
    db.session.delete(group)
    db.session.commit()
    
    # Log action
    AuditLog.log_action(
        user_id=current_user.id,
        action='Group Deleted',
        target=f'Group: {group_name}',
        details=f'Group deleted',
        ip_address=get_client_ip()
    )
    
    flash(f'Group {group_name} has been deleted successfully.', 'success')
    return redirect(url_for('groups'))

@app.route('/groups/<int:id>/members')
@admin_required
def group_members(id):
    """View and manage group members."""
    group = Group.query.get_or_404(id)
    form = AddUserToGroupForm(group=group)
    
    # Get search and page parameters
    search = request.args.get('search', '', type=str)
    page = request.args.get('page', 1, type=int)
    
    # Filter members based on search and paginate
    query = User.query.filter(User.groups.any(id=id))
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search)
            )
        )
    
    pagination = query.order_by(User.username).paginate(
        page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False
    )
    
    return render_template('group_members.html', title=f'Manage Members - {group.name}', 
                         group=group, members=pagination.items, pagination=pagination, form=form, search=search)

@app.route('/groups/<int:id>/add-member', methods=['POST'])
@admin_required
@read_write_required
def add_user_to_group(id):
    """Add a user to a group."""
    group = Group.query.get_or_404(id)
    form = AddUserToGroupForm(group=group)
    
    if form.validate_on_submit():
        user = User.query.get_or_404(form.user_id.data)
        
        # Check if user is already in group
        if user in group.members:
            flash(f'User {user.username} is already in this group.', 'warning')
        else:
            # Add user to group with role
            group.members.append(user)
            db.session.commit()
            
            # Log action
            AuditLog.log_action(
                user_id=current_user.id,
                action='User Added to Group',
                target=f'Group: {group.name}',
                details=f'User {user.username} added with role: {form.role.data}',
                ip_address=get_client_ip()
            )
            
            flash(f'User {user.username} has been added to group {group.name} successfully.', 'success')
    else:
        flash('Failed to add user to group.', 'error')
    
    return redirect(url_for('group_members', id=group.id))

@app.route('/groups/<int:group_id>/remove-member/<int:user_id>', methods=['POST'])
@admin_required
@read_write_required
def remove_user_from_group(group_id, user_id):
    """Remove a user from a group."""
    group = Group.query.get_or_404(group_id)
    user = User.query.get_or_404(user_id)
    
    # Check if user is in group
    if user in group.members:
        group.members.remove(user)
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='User Removed from Group',
            target=f'Group: {group.name}',
            details=f'User {user.username} removed from group',
            ip_address=get_client_ip()
        )
        
        flash(f'User {user.username} has been removed from group {group.name}.', 'success')
    else:
        flash(f'User {user.username} is not in this group.', 'error')
    
    return redirect(url_for('group_members', id=group_id))

@app.route('/groups/<int:id>/search-users')
@admin_required
def search_group_users(id):
    """API endpoint to search users for adding to group."""
    group = Group.query.get_or_404(id)
    query = request.args.get('q', '', type=str)
    
    # Get users not already in the group
    existing_user_ids = {member.id for member in group.members}
    available_users = User.query.filter(~User.id.in_(existing_user_ids)).all()
    
    # Filter based on search query
    filtered_users = []
    if query:
        filtered_users = [u for u in available_users if query.lower() in u.username.lower() or query.lower() in u.email.lower()]
    else:
        filtered_users = available_users
    
    results = [{'id': u.id, 'username': u.username, 'email': u.email} for u in filtered_users[:10]]
    return jsonify(results)

@app.route('/computers')
@login_required_with_message
def computers():
    """Computer management page."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Computer.query
    if search:
        query = query.filter(Computer.name.contains(search))
    
    computers_pagination = query.order_by(Computer.name).paginate(
        page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False
    )
    
    return render_template('computers.html', title='Computer Management',
                         computers=computers_pagination.items, pagination=computers_pagination, search=search)

@app.route('/computers/add', methods=['GET', 'POST'])
@admin_required
@read_write_required
def add_computer():
    """Add new computer."""
    form = ComputerForm()
    
    if request.method == 'GET' and 'ou_id' in request.args:
        try:
            form.ou_id.data = int(request.args.get('ou_id'))
        except ValueError:
            pass
            
    if form.validate_on_submit():
        computer = Computer(
            name=form.name.data,
            description=form.description.data,
            operating_system=form.operating_system.data,
            ip_address=form.ip_address.data,
            status=form.status.data,
            ou_id=form.ou_id.data if form.ou_id.data != 0 else None
        )
        
        db.session.add(computer)
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='Computer Created',
            target=f'Computer: {computer.name}',
            details=f'New computer added with status: {computer.status}',
            ip_address=get_client_ip()
        )
        
        flash(f'Computer {computer.name} has been created successfully.', 'success')
        return redirect(url_for('computers'))
    
    return render_template('computer_form.html', title='Add Computer', form=form, action='Add')

@app.route('/computers/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
@read_write_required
def edit_computer(id):
    """Edit existing computer."""
    computer = Computer.query.get_or_404(id)
    form = ComputerForm(original_computer=computer, obj=computer)
    
    if form.validate_on_submit():
        old_status = computer.status
        computer.name = form.name.data
        computer.description = form.description.data
        computer.operating_system = form.operating_system.data
        computer.ip_address = form.ip_address.data
        computer.status = form.status.data
        computer.ou_id = form.ou_id.data if form.ou_id.data != 0 else None
        
        db.session.commit()
        
        # Log action
        details = f'Computer information updated'
        if old_status != computer.status:
            details += f' - Status changed from {old_status} to {computer.status}'
        
        AuditLog.log_action(
            user_id=current_user.id,
            action='Computer Updated',
            target=f'Computer: {computer.name}',
            details=details,
            ip_address=get_client_ip()
        )
        
        flash(f'Computer {computer.name} has been updated successfully.', 'success')
        return redirect(url_for('computers'))
    
    return render_template('computer_form.html', title='Edit Computer', form=form, action='Edit', computer=computer)

@app.route('/computers/delete/<int:id>', methods=['POST'])
@admin_required
@read_write_required
def delete_computer(id):
    """Delete computer."""
    computer = Computer.query.get_or_404(id)
    computer_name = computer.name
    
    db.session.delete(computer)
    db.session.commit()
    
    # Log action
    AuditLog.log_action(
        user_id=current_user.id,
        action='Computer Deleted',
        target=f'Computer: {computer_name}',
        details=f'Computer removed from system',
        ip_address=get_client_ip()
    )
    
    flash(f'Computer {computer_name} has been deleted successfully.', 'success')
    return redirect(url_for('computers'))

@app.route('/computers/status/<int:id>/<status>', methods=['POST'])
@admin_required
def change_computer_status(id, status):
    """Change computer status."""
    if status not in ['ON', 'OFF', 'RESTART']:
        flash('Invalid status.', 'error')
        return redirect(url_for('computers'))
    
    computer = Computer.query.get_or_404(id)
    old_status = computer.status
    computer.status = status
    computer.last_seen = datetime.utcnow() if status == 'ON' else None
    
    db.session.commit()
    
    # Log action
    AuditLog.log_action(
        user_id=current_user.id,
        action=f'Computer {status}',
        target=f'Computer: {computer.name}',
        details=f'Status changed from {old_status} to {status}',
        ip_address=get_client_ip()
    )
    
    flash(f'Computer {computer.name} status changed to {status}.', 'success')
    return redirect(url_for('computers'))

@app.route('/api/computers/<int:id>/status', methods=['POST'])
@admin_required
def api_change_computer_status(id):
    """API endpoint to change computer status."""
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status required'}), 400
        
    status = data['status']
    if status not in ['ON', 'OFF', 'RESTART']:
        return jsonify({'error': 'Invalid status'}), 400
        
    computer = Computer.query.get_or_404(id)
    old_status = computer.status
    computer.status = status
    computer.last_seen = datetime.utcnow() if status == 'ON' else None
    
    db.session.commit()
    
    # Log action
    AuditLog.log_action(
        user_id=current_user.id,
        action=f'Computer {status}',
        target=f'Computer: {computer.name}',
        details=f'Status changed from {old_status} to {status} via API',
        ip_address=get_client_ip()
    )
    
    return jsonify({'success': True, 'status': status})

@app.route('/logs')
@login_required_with_message
def audit_logs():
    """Audit logs page."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = AuditLog.query
    if search:
        query = query.filter(
            (AuditLog.action.contains(search)) |
            (AuditLog.target.contains(search)) |
            (AuditLog.details.contains(search))
        )
    
    logs_pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False
    )
    
    return render_template('logs.html', title='Audit Logs',
                         logs=logs_pagination.items, pagination=logs_pagination, search=search)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # ✅ correct
    app.run(debug=True, port=5001)
