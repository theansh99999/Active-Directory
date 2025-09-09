"""
Forms for the Active Directory Clone application.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
from models import User, Group, OrganizationalUnit, Computer

class LoginForm(FlaskForm):
    """User login form."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class AdminPasswordResetForm(FlaskForm):
    """Admin password reset form for login page."""
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.'),
        Regexp(r'(?=.*[A-Z])', message='Password must contain at least one uppercase letter.'),
        Regexp(r'(?=.*\d)', message='Password must contain at least one number.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Admin Password')

class UserForm(FlaskForm):
    """User creation and editing form."""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    password = PasswordField('Password', validators=[
        Length(min=8, message='Password must be at least 8 characters long.'),
        Regexp(r'(?=.*[A-Z])', message='Password must contain at least one uppercase letter.'),
        Regexp(r'(?=.*\d)', message='Password must contain at least one number.')
    ])
    role = SelectField('Role', choices=[('User', 'User'), ('Admin', 'Admin')], validators=[DataRequired()])
    is_active = BooleanField('Active Account', default=True)
    submit = SubmitField('Save User')
    
    def __init__(self, original_user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_user = original_user
        
        # Make password optional for editing existing users
        if original_user:
            self.password.validators = [
                Length(min=8, message='Password must be at least 8 characters long.'),
                Regexp(r'(?=.*[A-Z])', message='Password must contain at least one uppercase letter.'),
                Regexp(r'(?=.*\d)', message='Password must contain at least one number.')
            ]
        else:
            self.password.validators.insert(0, DataRequired())
    
    def validate_username(self, username):
        if self.original_user is None or username.data != self.original_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Username already exists. Please choose a different username.')
    
    def validate_email(self, email):
        if self.original_user is None or email.data != self.original_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Email already registered. Please choose a different email.')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('user', 'User')], validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')
class PasswordResetForm(FlaskForm):
    """Password reset form for admin use."""
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.'),
        Regexp(r'(?=.*[A-Z])', message='Password must contain at least one uppercase letter.'),
        Regexp(r'(?=.*\d)', message='Password must contain at least one number.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')

class GroupForm(FlaskForm):
    """Group creation and editing form."""
    name = StringField('Group Name', validators=[DataRequired(), Length(min=3, max=50)])
    description = TextAreaField('Description', validators=[Length(max=200)])
    permissions = SelectField('Permissions', 
                            choices=[('read-only', 'Read Only'), ('read-write', 'Read Write')], 
                            validators=[DataRequired()])
    submit = SubmitField('Save Group')
    
    def __init__(self, original_group=None, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.original_group = original_group
    
    def validate_name(self, name):
        if self.original_group is None or name.data != self.original_group.name:
            group = Group.query.filter_by(name=name.data).first()
            if group is not None:
                raise ValidationError('Group name already exists. Please choose a different name.')

class OrganizationalUnitForm(FlaskForm):
    """Organizational Unit creation and editing form."""
    name = StringField('OU Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Length(max=200)])
    parent_id = SelectField('Parent OU', coerce=int, validators=[])
    submit = SubmitField('Save OU')
    
    def __init__(self, original_ou=None, *args, **kwargs):
        super(OrganizationalUnitForm, self).__init__(*args, **kwargs)
        self.original_ou = original_ou
        
        # Populate parent OU choices
        ous = OrganizationalUnit.query.all()
        choices = [(0, 'None (Root Level)')]
        
        for ou in ous:
            # Don't allow selecting self as parent when editing
            if original_ou is None or ou.id != original_ou.id:
                choices.append((ou.id, ou.name))
        
        self.parent_id.choices = choices
    
    def validate_name(self, name):
        if self.original_ou is None or name.data != self.original_ou.name:
            ou = OrganizationalUnit.query.filter_by(name=name.data).first()
            if ou is not None:
                raise ValidationError('OU name already exists. Please choose a different name.')

class ComputerForm(FlaskForm):
    """Computer creation and editing form."""
    name = StringField('Computer Name', validators=[DataRequired(), Length(min=3, max=50)])
    description = TextAreaField('Description', validators=[Length(max=200)])
    operating_system = StringField('Operating System', validators=[DataRequired(), Length(max=100)])
    ip_address = StringField('IP Address', validators=[DataRequired(), Length(max=15)])
    status = SelectField('Status', 
                        choices=[('ON', 'ON'), ('OFF', 'OFF'), ('RESTART', 'RESTART')], 
                        validators=[DataRequired()])
    ou_id = SelectField('Organizational Unit', coerce=int, validators=[])
    submit = SubmitField('Save Computer')
    
    def __init__(self, original_computer=None, *args, **kwargs):
        super(ComputerForm, self).__init__(*args, **kwargs)
        self.original_computer = original_computer
        
        # Populate OU choices
        ous = OrganizationalUnit.query.all()
        choices = [(0, 'None')]
        for ou in ous:
            choices.append((ou.id, ou.name))
        
        self.ou_id.choices = choices
    
    def validate_name(self, name):
        if self.original_computer is None or name.data != self.original_computer.name:
            computer = Computer.query.filter_by(name=name.data).first()
            if computer is not None:
                raise ValidationError('Computer name already exists. Please choose a different name.')
    
    def validate_ip_address(self, ip_address):
        if self.original_computer is None or ip_address.data != self.original_computer.ip_address:
            computer = Computer.query.filter_by(ip_address=ip_address.data).first()
            if computer is not None:
                raise ValidationError('IP address already in use. Please choose a different IP address.')