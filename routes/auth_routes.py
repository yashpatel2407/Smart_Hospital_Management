"""
Authentication Routes - Login, Register, Logout
Uses Flask session (dictionary) for auth state management.
Uses Werkzeug for password hashing.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from db import mysql, mail
import random
import time
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard_redirect'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('auth/login.html')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND is_active = 1", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password_hash'], password):
            # Store user data in session dictionary
            session['user_id'] = user['id']
            session['full_name'] = user['full_name']
            session['email'] = user['email']
            session['role'] = user['role']
            session['profile_image'] = user.get('profile_image', '')

            flash(f'Welcome back, {user["full_name"]}!', 'success')

            # Role-based redirect
            return redirect(url_for('dashboard_redirect'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard_redirect'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        gender = request.form.get('gender', '')
        dob = request.form.get('date_of_birth', '')
        blood_group = request.form.get('blood_group', '')

        # Validation
        if not all([full_name, email, phone, password, confirm_password]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register.html')

        # Phone validation: Must be 10 digits and not start with 0
        if not (phone.isdigit() and len(phone) == 10 and phone[0] != '0'):
            flash('Invalid phone number. It must be 10 digits and not start with 0.', 'danger')
            return render_template('auth/register.html')

        # Check if DOB is in the future
        if dob:
            selected_dob = datetime.strptime(dob, '%Y-%m-%d').date()
            if selected_dob > datetime.now().date():
                flash('Date of Birth cannot be in the future.', 'danger')
                return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register.html')

        cur = mysql.connection.cursor()

        # Check if email exists
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            flash('Email already registered.', 'danger')
            cur.close()
            return render_template('auth/register.html')

        # Hash password
        hashed_password = generate_password_hash(password)

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        # Store registration data in session
        session['reg_data'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'password_hash': hashed_password,
            'gender': gender,
            'dob': dob,
            'blood_group': blood_group,
            'otp': otp,
            'otp_time': time.time()
        }

        # Send OTP via Email
        try:
            msg = Message('Email Verification - SmartCare HMS',
                          recipients=[email])
            msg.body = f"Hello {full_name},\n\nYour OTP for registration at SmartCare Hospital Management System is: {otp}\n\nThis OTP is valid for 10 minutes.\n\nThank you!"
            mail.send(msg)
            flash('An OTP has been sent to your email. Please verify.', 'info')
            return redirect(url_for('auth.verify_otp'))
        except Exception as e:
            print(f"Mail Error: {e}")
            flash('Error sending email. Please check your config or try again.', 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'reg_data' not in session:
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        user_otp = request.form.get('otp', '').strip()
        reg_data = session['reg_data']

        # Check age - 10 min window
        if time.time() - reg_data['otp_time'] > 600:
            session.pop('reg_data')
            flash('OTP expired. Please register again.', 'danger')
            return redirect(url_for('auth.register'))

        if user_otp == reg_data['otp']:
            # OTP Correct -> Create Account
            try:
                # Ensure connection is alive to prevent "Server has gone away"
                mysql.connection.ping(True)
                cur = mysql.connection.cursor()
                
                cur.execute("""
                    INSERT INTO users (full_name, email, phone, password_hash, role, gender, date_of_birth, is_active)
                    VALUES (%s, %s, %s, %s, 'patient', %s, %s, 1)
                """, (reg_data['full_name'], reg_data['email'], reg_data['phone'], 
                      reg_data['password_hash'], reg_data['gender'] or None, reg_data['dob'] or None))
                
                user_id = cur.lastrowid
                
                cur.execute("""
                    INSERT INTO patients (user_id, blood_group)
                    VALUES (%s, %s)
                """, (user_id, reg_data['blood_group'] or None))
                
                mysql.connection.commit()
                
                # Auto-login after verification
                session['user_id'] = user_id
                session['full_name'] = reg_data['full_name']
                session['email'] = reg_data['email']
                session['role'] = 'patient'
                session['profile_image'] = ''
                
                session.pop('reg_data')
                flash('Email verified! Registration successful. Welcome to SmartCare!', 'success')
                return redirect(url_for('dashboard_redirect'))
            except Exception as e:
                flash(f'Database Error: {e}', 'danger')
                print(f"Auth DB Error: {e}")
            finally:
                if 'cur' in locals():
                    cur.close()
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('auth/verify_otp.html')


@auth_bp.route('/logout')
def logout():
    session.clear()  # Clear session dictionary
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
