"""
Authentication routes for Easy Clinic Portal.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFError
from app import db
from app.auth.forms import LoginForm, RegistrationForm
from app.models.user import User, Role, PatientProfile

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# CSRF error handler
@auth_bp.errorhandler(CSRFError)
def handle_csrf_error(_):
    flash('CSRF token validation failed. Please try again.', 'danger')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        # Redirect based on user role
        if current_user.is_patient():
            return redirect(url_for('patients.dashboard'))
        elif current_user.is_doctor():
            return redirect(url_for('doctors.dashboard'))
        elif current_user.is_assistant():
            return redirect(url_for('assistants.dashboard'))
        elif current_user.is_admin() or current_user.is_superadmin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('auth.login'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        print(f"Login attempt: {form.email.data}, User found: {user is not None}")
        if user:
            # Check if user is active
            if not user.is_active and not user.is_superadmin():
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return render_template('auth/login.html', form=form, title='Login')

            password_valid = user.verify_password(form.password.data)
            print(f"Password valid: {password_valid}, Role: {user.role if user else None}")
            if password_valid:
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')

                # Redirect based on user role
                if not next_page or next_page.startswith('/'):
                    if user.is_patient():
                        next_page = url_for('patients.dashboard')
                    elif user.is_doctor():
                        next_page = url_for('doctors.dashboard')
                    elif user.is_assistant():
                        next_page = url_for('assistants.dashboard')
                    elif user.is_admin() or user.is_superadmin():
                        next_page = url_for('admin.dashboard')

                return redirect(next_page)
            else:
                flash('Invalid password.', 'danger')
        else:
            flash('Email not found.', 'danger')

    return render_template('auth/login.html', form=form, title='Login')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle patient registration."""
    if current_user.is_authenticated:
        # Redirect based on user role
        if current_user.is_patient():
            return redirect(url_for('patients.dashboard'))
        elif current_user.is_doctor():
            return redirect(url_for('doctors.dashboard'))
        elif current_user.is_assistant():
            return redirect(url_for('assistants.dashboard'))
        elif current_user.is_admin() or current_user.is_superadmin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('auth.login'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new patient user
        user = User(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,
            role=Role.PATIENT
        )

        # Create patient profile
        profile = PatientProfile(user=user)

        # Add to database
        db.session.add(user)
        db.session.add(profile)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title='Register')
