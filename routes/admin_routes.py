"""
Admin Routes - Dashboard, Manage Doctors/Patients/Appointments/Pharmacy/Billing/Reports
Uses: Queue (appointment_queue), Merge Sort (sort_appointments),
      Linear Search, Session Dictionary
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from flask_mail import Message
from db import mysql, mail
from utils.auth import role_required
from utils.data_structures import (
    appointment_queue, sort_appointments,
    linear_search_patients
)

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')


@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    cur = mysql.connection.cursor()

    # Stats using COUNT queries
    cur.execute("SELECT COUNT(*) as count FROM patients")
    total_patients = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) as count FROM doctors")
    total_doctors = cur.fetchone()['count']

    cur.execute("SELECT COUNT(*) as count FROM appointments")
    total_appointments = cur.fetchone()['count']

    cur.execute("SELECT COALESCE(SUM(net_amount),0) as total FROM bills WHERE payment_status='paid'")
    total_revenue = cur.fetchone()['total']

    # Recent appointments (list) - sorted using merge sort
    cur.execute("""
        SELECT a.*, u1.full_name as patient_name, u2.full_name as doctor_name,
               d.specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u1 ON p.user_id = u1.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u2 ON d.user_id = u2.id
        ORDER BY a.created_at DESC LIMIT 10
    """)
    recent_appointments = cur.fetchall()

    # Sort appointments using merge sort (data structure)
    recent_appointments = sort_appointments(list(recent_appointments), key='appointment_date', reverse=True)

    # Recent patients (list)
    cur.execute("""
        SELECT u.*, p.blood_group, p.id as patient_id
        FROM users u JOIN patients p ON u.id = p.user_id
        ORDER BY u.created_at DESC LIMIT 10
    """)
    recent_patients = cur.fetchall()

    # --- ANALYTICS DATA ---
    # Day-wise Trends (Last 7 Days)
    cur.execute("""
        SELECT DATE_FORMAT(appointment_date, '%b %d') as label, COUNT(*) as count 
        FROM appointments 
        WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY appointment_date ORDER BY appointment_date
    """)
    day_trends = cur.fetchall()
    
    # Week-wise Trends (Current Year)
    cur.execute("""
        SELECT CONCAT('Wk ', WEEK(appointment_date)) as label, COUNT(*) as count 
        FROM appointments WHERE YEAR(appointment_date) = YEAR(CURDATE())
        GROUP BY WEEK(appointment_date) ORDER BY WEEK(appointment_date)
    """)
    week_trends = cur.fetchall()
    
    # Month-wise Trends (Current Year)
    cur.execute("""
        SELECT DATE_FORMAT(appointment_date, '%b') as label, COUNT(*) as count 
        FROM appointments WHERE YEAR(appointment_date) = YEAR(CURDATE())
        GROUP BY MONTH(appointment_date) ORDER BY MONTH(appointment_date)
    """)
    month_trends = cur.fetchall()
    
    # Peak Analysis
    cur.execute("SELECT DAYNAME(appointment_date) as day, COUNT(*) as count FROM appointments GROUP BY day ORDER BY count DESC LIMIT 1")
    peak_day_res = cur.fetchone()
    peak_day = peak_day_res['day'] if peak_day_res else "N/A"
    
    cur.execute("SELECT HOUR(appointment_time) as hour, COUNT(*) as count FROM appointments GROUP BY hour ORDER BY count DESC LIMIT 1")
    peak_hour_res = cur.fetchone()
    peak_time = f"{peak_hour_res['hour']:02d}:00" if peak_hour_res else "N/A"

    # Time Range Filter for Charts
    trend_range = request.args.get('range', 'month')
    date_filter = ""
    if trend_range == 'day':
        date_filter = "WHERE appointment_date = CURDATE()"
    elif trend_range == 'week':
        date_filter = "WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
    else:  # month
        date_filter = "WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"

    # Chart data: appointment status breakdown within selected range
    cur.execute(f"SELECT status, COUNT(*) as count FROM appointments {date_filter} GROUP BY status")
    status_data = cur.fetchall()
    chart_labels = [r['status'].capitalize() for r in status_data]
    chart_values = [r['count'] for r in status_data]

    # Chart data: departments (specializations)
    cur.execute("""
        SELECT d.specialization, COUNT(a.id) as count
        FROM doctors d
        LEFT JOIN appointments a ON d.id = a.doctor_id
        GROUP BY d.specialization
        HAVING count > 0
        ORDER BY count DESC
    """)
    dept_data = cur.fetchall()
    dept_labels = [r['specialization'] for r in dept_data]
    dept_values = [r['count'] for r in dept_data]

    # Queue: load pending appointments into queue
    cur.execute("""
        SELECT a.id, u.full_name as patient_name, a.appointment_date, a.status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE a.status = 'pending'
        ORDER BY a.created_at ASC
    """)
    pending = cur.fetchall()
    # Rebuild queue with pending appointments
    appointment_queue._queue.clear()
    for apt in pending:
        appointment_queue.enqueue(dict(apt))

    queue_size = appointment_queue.size()
    cur.close()

    return render_template('admin/dashboard.html',
                           active_page='dashboard',
                           total_patients=total_patients,
                           total_doctors=total_doctors,
                           total_appointments=total_appointments,
                           total_revenue=total_revenue,
                           recent_appointments=recent_appointments,
                           recent_patients=recent_patients,
                           chart_labels=chart_labels,
                           chart_values=chart_values,
                           dept_labels=dept_labels,
                           dept_values=dept_values,
                           day_trends=day_trends,
                           week_trends=week_trends,
                           month_trends=month_trends,
                           peak_day=peak_day,
                           peak_time=peak_time,
                           queue_size=queue_size,
                           trend_range=trend_range)


@admin_bp.route('/patients')
@role_required('admin')
def patients():
    cur = mysql.connection.cursor()
    search = request.args.get('search', '').strip()

    cur.execute("""
        SELECT u.*, p.blood_group, p.emergency_contact, p.id as patient_id
        FROM users u JOIN patients p ON u.id = p.user_id
        ORDER BY u.created_at DESC
    """)
    all_patients = cur.fetchall()
    cur.close()

    # Linear search (data structure) if search term provided
    if search:
        all_patients = linear_search_patients(list(all_patients), search)

    return render_template('admin/patients.html',
                           active_page='patients',
                           patients=all_patients, search=search)


@admin_bp.route('/doctors', methods=['GET', 'POST'])
@role_required('admin')
def doctors():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        specialization = request.form.get('specialization', '').strip()
        qual_select = request.form.get('qualification_select', '').strip()
        qual_manual = request.form.get('qualification_manual', '').strip()
        experience = request.form.get('experience_years', 0)
        fee = request.form.get('consultation_fee', 0)

        # Handle qualification logic
        qualification = qual_manual if qual_select == 'Other' else qual_select

        # Phone validation: Must be 10 digits and not start with 0
        is_phone_valid = phone.isdigit() and len(phone) == 10 and phone[0] != '0'

        if not all([name, email, phone, password, specialization, qualification]):
            flash('Please fill all required fields.', 'danger')
        elif not is_phone_valid:
            flash('Invalid phone number. It must be 10 digits and not start with 0.', 'danger')
        else:
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                flash('Email already exists.', 'danger')
            else:
                hashed = generate_password_hash(password)
                cur.execute("""
                    INSERT INTO users (full_name,email,phone,password_hash,role,is_active)
                    VALUES (%s,%s,%s,%s,'doctor',1)
                """, (name, email, phone, hashed))
                mysql.connection.commit()
                uid = cur.lastrowid

                cur.execute("""
                    INSERT INTO doctors (user_id,specialization,qualification,experience_years,consultation_fee)
                    VALUES (%s,%s,%s,%s,%s)
                """, (uid, specialization, qualification, int(experience), float(fee)))
                mysql.connection.commit()
                flash('Doctor added successfully!', 'success')

    cur.execute("""
        SELECT u.*, d.specialization, d.qualification, d.experience_years,
               d.consultation_fee, d.id as doctor_id
        FROM users u JOIN doctors d ON u.id = d.user_id
        ORDER BY u.created_at DESC
    """)
    doctors_list = cur.fetchall()
    cur.close()

    return render_template('admin/doctors.html',
                           active_page='doctors', doctors=doctors_list)


@admin_bp.route('/doctors/remove/<int:doc_id>')
@role_required('admin')
def remove_doctor(doc_id):
    cur = mysql.connection.cursor()
    
    # Get user_id associated with this doctor
    cur.execute("SELECT user_id FROM doctors WHERE id = %s", (doc_id,))
    doctor = cur.fetchone()
    
    if doctor:
        user_id = doctor['user_id']
        # Deleting the user will cascade delete the doctor record due to FOREIGN KEY ... ON DELETE CASCADE
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        flash('Doctor and associated user account removed successfully.', 'success')
    else:
        flash('Doctor not found.', 'danger')
        
    cur.close()
    return redirect(url_for('admin.doctors'))


@admin_bp.route('/appointments')
@role_required('admin')
def appointments():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT a.*, u1.full_name as patient_name, u2.full_name as doctor_name,
               d.specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u1 ON p.user_id = u1.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u2 ON d.user_id = u2.id
        ORDER BY a.appointment_date DESC
    """)
    appointments_list = sort_appointments(list(cur.fetchall()), key='appointment_date', reverse=True)
    cur.close()

    return render_template('admin/appointments.html',
                           active_page='appointments', appointments=appointments_list)


@admin_bp.route('/pharmacy', methods=['GET', 'POST'])
@role_required('admin')
def pharmacy():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        manufacturer = request.form.get('manufacturer', '').strip()
        price = request.form.get('price', 0)
        stock = request.form.get('stock_quantity', 0)
        expiry = request.form.get('expiry_date', '')
        desc = request.form.get('description', '').strip()

        if not name or not price:
            flash('Medicine name and price are required.', 'danger')
        else:
            cur.execute("""
                INSERT INTO medicines (name,category,manufacturer,price,stock_quantity,expiry_date,description)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (name, category, manufacturer, float(price), int(stock), expiry or None, desc))
            mysql.connection.commit()
            flash('Medicine added successfully!', 'success')

    cur.execute("SELECT * FROM medicines ORDER BY name ASC")
    medicines = cur.fetchall()
    cur.close()

    return render_template('admin/pharmacy.html',
                           active_page='pharmacy', medicines=medicines)


@admin_bp.route('/pharmacy/update/<int:mid>', methods=['POST'])
@role_required('admin')
def update_medicine(mid):
    stock = request.form.get('stock_quantity', 0)
    price = request.form.get('price', 0)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE medicines SET stock_quantity=%s, price=%s WHERE id=%s",
                (int(stock), float(price), mid))
    mysql.connection.commit()
    cur.close()
    flash('Medicine updated.', 'success')
    return redirect(url_for('admin.pharmacy'))


@admin_bp.route('/billing', methods=['GET', 'POST'])
@role_required('admin')
def billing():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        appointment_id = request.form.get('appointment_id') or None
        total = float(request.form.get('total_amount', 0))
        discount = float(request.form.get('discount', 0))
        tax = float(request.form.get('tax', 0))
        net = total - discount + tax
        method = request.form.get('payment_method', 'cash')
        status = request.form.get('payment_status', 'unpaid')

        cur.execute("""
            INSERT INTO bills (patient_id,appointment_id,total_amount,discount,tax,net_amount,payment_status,payment_method)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (patient_id, appointment_id, total, discount, tax, net, status, method))
        mysql.connection.commit()
        flash('Bill created successfully!', 'success')

    cur.execute("""
        SELECT b.*, u.full_name as patient_name
        FROM bills b
        JOIN patients p ON b.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        ORDER BY b.created_at DESC
    """)
    bills = cur.fetchall()

    cur.execute("SELECT p.id, u.full_name FROM patients p JOIN users u ON p.user_id=u.id")
    patients_list = cur.fetchall()
    cur.close()

    return render_template('admin/billing.html',
                           active_page='billing', bills=bills, patients=patients_list)


@admin_bp.route('/reports')
@role_required('admin')
def reports():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT r.*, u1.full_name as patient_name,
               COALESCE(u2.full_name,'N/A') as doctor_name
        FROM medical_reports r
        JOIN patients p ON r.patient_id = p.id
        JOIN users u1 ON p.user_id = u1.id
        LEFT JOIN doctors d ON r.doctor_id = d.id
        LEFT JOIN users u2 ON d.user_id = u2.id
        ORDER BY r.created_at DESC
    """)
    reports_list = cur.fetchall()
    cur.close()

    return render_template('admin/reports.html',
                           active_page='reports', reports=reports_list)


@admin_bp.route('/manage-leaves')
@role_required('admin')
def manage_leaves():
    cur = mysql.connection.cursor()
    # Get all pending leaves with doctor details
    cur.execute("""
        SELECT du.*, u.full_name as doctor_name, d.specialization
        FROM doctor_unavailability du
        JOIN doctors d ON du.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        WHERE du.status = 'pending'
        ORDER BY du.unavailable_date ASC
    """)
    pending_leaves = cur.fetchall()
    
    # Get history (last 20 approved/rejected)
    cur.execute("""
        SELECT du.*, u.full_name as doctor_name, d.specialization
        FROM doctor_unavailability du
        JOIN doctors d ON du.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        WHERE du.status != 'pending'
        ORDER BY du.updated_at DESC LIMIT 20
    """)
    leave_history = cur.fetchall()
    cur.close()
    
    return render_template('admin/manage_leaves.html', 
                         active_page='leaves', 
                         pending_leaves=pending_leaves,
                         leave_history=leave_history)

@admin_bp.route('/leaves/approve/<int:leave_id>')
@role_required('admin')
def approve_leave(leave_id):
    cur = mysql.connection.cursor()
    # 1. Get leave details
    cur.execute("SELECT * FROM doctor_unavailability WHERE id = %s", (leave_id,))
    leave = cur.fetchone()
    
    if not leave:
        flash('Leave request not found.', 'danger')
        return redirect(url_for('admin.manage_leaves'))
        
    date = leave['unavailable_date']
    doctor_id = leave['doctor_id']
    reason = leave['reason']
    
    try:
        # 2. Update Leave Status
        cur.execute("UPDATE doctor_unavailability SET status = 'approved' WHERE id = %s", (leave_id,))
        
        # 3. Get all shared appointments for this doctor on this day
        cur.execute("""
            SELECT a.id, u.email, u.full_name, a.appointment_time
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE a.doctor_id = %s AND a.appointment_date = %s AND a.status IN ('pending', 'confirmed')
        """, (doctor_id, date))
        affected_appts = cur.fetchall()
        
        # 4. Cancel appointments and Notify
        for appt in affected_appts:
            cur.execute("UPDATE appointments SET status='cancelled', notes=%s WHERE id=%s", 
                        (f"Doctor Leave Approved: {reason}", appt['id']))
            try:
                msg = Message('Appointment Cancellation - SmartCare Hospital',
                              recipients=[appt['email']])
                msg.body = f"Hello {appt['full_name']},\n\nWe regret to inform you that your appointment scheduled for {date} at {appt['appointment_time']} has been cancelled as the doctor's leave for this date has been approved.\n\nReason: {reason}\n\nPlease book another slot. We apologize for the discomfort.\n\nRegards,\nSmartCare Hospital Team"
                mail.send(msg)
            except Exception as mail_err:
                print(f"Mail Error: {mail_err}")
                
        mysql.connection.commit()
        flash(f'Leave approved and {len(affected_appts)} appointments cancelled.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error approving leave: {e}', 'danger')
        
    cur.close()
    return redirect(url_for('admin.manage_leaves'))

@admin_bp.route('/leaves/reject/<int:leave_id>')
@role_required('admin')
def reject_leave(leave_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE doctor_unavailability SET status = 'rejected' WHERE id = %s", (leave_id,))
    mysql.connection.commit()
    cur.close()
    flash('Leave request rejected.', 'info')
    return redirect(url_for('admin.manage_leaves'))
