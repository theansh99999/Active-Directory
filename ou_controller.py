from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user

from forms import OrganizationalUnitForm
from auth import admin_required, read_write_required, get_client_ip, login_required_with_message
from models import AuditLog, OrganizationalUnit, User, Group, Computer, db
from ou_service import OUService, OUServiceError

ou_bp = Blueprint('ou_bp', __name__)

# --- API Endpoints ---

@ou_bp.route('/api/ous/tree', methods=['GET'])
@login_required_with_message
def api_get_ou_tree():
    """Return the complete OU hierarchy as a tree."""
    tree = OUService.get_tree()
    return jsonify(tree)

@ou_bp.route('/api/ous/<int:id>/objects', methods=['GET'])
@login_required_with_message
def api_get_ou_objects(id):
    """Fetch all Users, Groups, Computers, and Child OUs inside a selected OU."""
    try:
        objects = OUService.get_ou_objects(id)
        return jsonify(objects)
    except OUServiceError as e:
        return jsonify({"error": str(e)}), 400

@ou_bp.route('/api/ous/<int:id>/search-unassigned', methods=['GET'])
@login_required_with_message
def api_search_unassigned_objects(id):
    """Fetch objects that are not currently assigned to this OU."""
    from flask import current_app
    obj_type = request.args.get('type')
    query_str = request.args.get('q', '').lower()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ITEMS_PER_PAGE']
    
    results = []
    
    if obj_type == 'user':
        query = User.query.filter((User.ou_id != id) | (User.ou_id.is_(None)))
        if query_str:
            query = query.filter(db.or_(
                User.username.ilike(f'%{query_str}%'),
                User.email.ilike(f'%{query_str}%'),
                User.first_name.ilike(f'%{query_str}%'),
                User.last_name.ilike(f'%{query_str}%')
            ))
        pagination = query.order_by(User.username).paginate(page=page, per_page=per_page, error_out=False)
        for u in pagination.items:
            current_ou = u.organizational_unit.name if u.organizational_unit else "None (Root)"
            results.append({"id": u.id, "name": u.username, "type_desc": u.email, "current_ou": current_ou})
            
    elif obj_type == 'group':
        query = Group.query.filter((Group.ou_id != id) | (Group.ou_id.is_(None)))
        if query_str:
            query = query.filter(Group.name.ilike(f'%{query_str}%'))
        pagination = query.order_by(Group.name).paginate(page=page, per_page=per_page, error_out=False)
        for g in pagination.items:
            current_ou = g.organizational_unit.name if g.organizational_unit else "None (Root)"
            results.append({"id": g.id, "name": g.name, "type_desc": "Group", "current_ou": current_ou})
            
    elif obj_type == 'computer':
        query = Computer.query.filter((Computer.ou_id != id) | (Computer.ou_id.is_(None)))
        if query_str:
            query = query.filter(db.or_(
                Computer.name.ilike(f'%{query_str}%'),
                Computer.ip_address.ilike(f'%{query_str}%')
            ))
        pagination = query.order_by(Computer.name).paginate(page=page, per_page=per_page, error_out=False)
        for c in pagination.items:
            current_ou = c.organizational_unit.name if c.organizational_unit else "None (Root)"
            results.append({"id": c.id, "name": c.name, "type_desc": c.operating_system, "current_ou": current_ou, "status": c.status})
            
    else:
        return jsonify({"error": "Invalid type"}), 400
        
    return jsonify({
        "items": results,
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    })

@ou_bp.route('/api/ous/<int:id>/assign-objects', methods=['POST'])
@admin_required
@read_write_required
def api_assign_objects(id):
    """Assign existing objects to this OU."""
    data = request.get_json()
    if not data or 'type' not in data or 'ids' not in data:
        return jsonify({"error": "Invalid request payload"}), 400
        
    obj_type = data['type']
    ids = data['ids']
    
    ou = OrganizationalUnit.query.get_or_404(id)
    
    count = 0
    if obj_type == 'user':
        users = User.query.filter(User.id.in_(ids)).all()
        for u in users:
            u.ou_id = id
            count += 1
    elif obj_type == 'group':
        groups = Group.query.filter(Group.id.in_(ids)).all()
        for g in groups:
            g.ou_id = id
            count += 1
    elif obj_type == 'computer':
        computers = Computer.query.filter(Computer.id.in_(ids)).all()
        for c in computers:
            c.ou_id = id
            count += 1
    else:
        return jsonify({"error": "Invalid type"}), 400
        
    db.session.commit()
    
    # Log action
    AuditLog.log_action(
        user_id=current_user.id,
        action='Objects Assigned to OU',
        target=f'OU: {ou.name}',
        details=f'{count} {obj_type}(s) assigned to OU via management console.',
        ip_address=get_client_ip()
    )
    
    return jsonify({"success": True, "count": count})

@ou_bp.route('/api/ous/<int:id>/remove-object', methods=['POST'])
@admin_required
@read_write_required
def api_remove_object(id):
    """Remove an object from this OU (sets ou_id to None)."""
    data = request.get_json()
    if not data or 'type' not in data or 'obj_id' not in data:
        return jsonify({"error": "Invalid request payload"}), 400
        
    obj_type = data['type']
    obj_id = data['obj_id']
    
    ou = OrganizationalUnit.query.get_or_404(id)
    target_name = ""
    
    if obj_type == 'user':
        obj = User.query.get_or_404(obj_id)
        if obj.ou_id == id:
            obj.ou_id = None
            target_name = f"User: {obj.username}"
    elif obj_type == 'group':
        obj = Group.query.get_or_404(obj_id)
        if obj.ou_id == id:
            obj.ou_id = None
            target_name = f"Group: {obj.name}"
    elif obj_type == 'computer':
        obj = Computer.query.get_or_404(obj_id)
        if obj.ou_id == id:
            obj.ou_id = None
            target_name = f"Computer: {obj.name}"
    else:
        return jsonify({"error": "Invalid type"}), 400
        
    db.session.commit()
    
    if target_name:
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='Object Removed from OU',
            target=target_name,
            details=f'{obj_type.capitalize()} removed from OU {ou.name} via management console.',
            ip_address=get_client_ip()
        )
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Object was not in this OU"}), 400

# --- Web Routes ---

@ou_bp.route('/ous')
@login_required_with_message
def organizational_units():
    """Organizational Units management page."""
    ous = OrganizationalUnit.query.order_by(OrganizationalUnit.name).all()
    return render_template('ous.html', title='Organizational Units', ous=ous)

@ou_bp.route('/ous/add', methods=['GET', 'POST'])
@admin_required
@read_write_required
def add_ou():
    """Add new organizational unit."""
    form = OrganizationalUnitForm()
    if form.validate_on_submit():
        try:
            parent_id = form.parent_id.data if form.parent_id.data != 0 else None
            ou = OUService.create_ou(
                name=form.name.data,
                description=form.description.data,
                parent_id=parent_id
            )
            
            # Log action
            AuditLog.log_action(
                user_id=current_user.id,
                action='OU Created',
                target=f'OU: {ou.name}',
                details=f'New organizational unit created',
                ip_address=get_client_ip()
            )
            
            flash(f'Organizational Unit {ou.name} has been created successfully.', 'success')
            return redirect(url_for('ou_bp.organizational_units', selected_ou=ou.id))
        except OUServiceError as e:
            flash(str(e), 'error')
    
    return render_template('ou_form.html', title='Add OU', form=form, action='Add')

@ou_bp.route('/ous/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
@read_write_required
def edit_ou(id):
    """Edit existing organizational unit."""
    ou = OrganizationalUnit.query.get_or_404(id)
    form = OrganizationalUnitForm(original_ou=ou, obj=ou)
    
    if form.validate_on_submit():
        try:
            parent_id = form.parent_id.data if form.parent_id.data != 0 else None
            updated_ou = OUService.update_ou(
                ou_id=id,
                name=form.name.data,
                description=form.description.data,
                parent_id=parent_id
            )
            
            # Log action
            AuditLog.log_action(
                user_id=current_user.id,
                action='OU Updated',
                target=f'OU: {updated_ou.name}',
                details=f'Organizational unit updated',
                ip_address=get_client_ip()
            )
            
            flash(f'Organizational Unit {updated_ou.name} has been updated successfully.', 'success')
            return redirect(url_for('ou_bp.organizational_units'))
        except OUServiceError as e:
            flash(str(e), 'error')
    
    return render_template('ou_form.html', title='Edit OU', form=form, action='Edit', ou=ou)

@ou_bp.route('/ous/delete/<int:id>', methods=['POST'])
@admin_required
@read_write_required
def delete_ou(id):
    """Delete organizational unit."""
    ou = OrganizationalUnit.query.get_or_404(id)
    ou_name = ou.name
    
    try:
        OUService.delete_ou(id)
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='OU Deleted',
            target=f'OU: {ou_name}',
            details=f'Organizational unit deleted',
            ip_address=get_client_ip()
        )
        
        flash(f'Organizational Unit {ou_name} has been deleted successfully.', 'success')
    except OUServiceError as e:
        flash(str(e), 'error')
        
    return redirect(url_for('ou_bp.organizational_units'))
