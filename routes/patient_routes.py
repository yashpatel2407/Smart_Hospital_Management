"""
Patient Routes - Dashboard, Book Appointment, View Status, Upload Reports, View Prescriptions
Uses: appointment_queue (queue), sort_appointments (merge sort), session dictionary
"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from werkzeug.utils import secure_filename
from db import mysql
from utils.auth import role_required
from utils.data_structures import appointment_queue, sort_appointments
from utils.ai_helper import ask_medical_bot
from datetime import datetime, time as dt_time

patient_bp = Blueprint('patient', __name__, template_folder='../templates/patient')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'png', 'jpg', 'jpeg'}


@patient_bp.route('/dashboard')
@role_required('patient')
def dashboard():
    cur = mysql.connection.cursor()
    user_id = session['user_id']

    cur.execute("SELECT id FROM patients WHERE user_id=%s", (user_id,))
    pat = cur.fetchone()
    if not pat:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('auth.logout'))
    patient_id = pat['id']

    # Stats
    cur.execute("SELECT COUNT(*) as c FROM appointments WHERE patient_id=%s", (patient_id,))
    total_appts = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) as c FROM appointments WHERE patient_id=%s AND status='pending'",
                (patient_id,))
    pending_appts = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) as c FROM prescriptions WHERE patient_id=%s", (patient_id,))
    total_prescriptions = cur.fetchone()['c']

    cur.execute("SELECT COALESCE(SUM(net_amount),0) as t FROM bills WHERE patient_id=%s AND payment_status='unpaid'",
                (patient_id,))
    pending_bills = cur.fetchone()['t']

    # Upcoming appointments
    cur.execute("""
        SELECT a.*, u.full_name as doctor_name, d.specialization
        FROM appointments a
        JOIN doctors d ON a.doctor_id=d.id
        JOIN users u ON d.user_id=u.id
        WHERE a.patient_id=%s AND a.appointment_date >= CURDATE()
        ORDER BY a.appointment_date ASC LIMIT 5
    """, (patient_id,))
    upcoming = list(cur.fetchall())

    # Rebuild queue from DB to ensure sync
    cur.execute("SELECT id, status FROM appointments WHERE status='pending' ORDER BY created_at ASC")
    pending_list = cur.fetchall()
    appointment_queue._queue.clear()
    for p in pending_list:
        appointment_queue.enqueue({'id': p['id']})

    # Queue position for pending appointments
    for apt in upcoming:
        if apt['status'] == 'pending':
            pos = appointment_queue.get_position(apt['id'])
            apt['queue_position'] = pos if pos > 0 else 'N/A'

    cur.close()
    return render_template('patient/dashboard.html',
                           active_page='dashboard',
                           total_appts=total_appts,
                           pending_appts=pending_appts,
                           total_prescriptions=total_prescriptions,
                           pending_bills=pending_bills,
                           upcoming=upcoming)


@patient_bp.route('/appointments')
@role_required('patient')
def appointments():
    cur = mysql.connection.cursor()
    user_id = session['user_id']
    cur.execute("SELECT id FROM patients WHERE user_id=%s", (user_id,))
    patient_id = cur.fetchone()['id']

    cur.execute("""
        SELECT a.*, u.full_name as doctor_name, d.specialization
        FROM appointments a
        JOIN doctors d ON a.doctor_id=d.id
        JOIN users u ON d.user_id=u.id
        WHERE a.patient_id=%s
        ORDER BY a.appointment_date DESC
    """, (patient_id,))
    appts = sort_appointments(list(cur.fetchall()), key='appointment_date', reverse=True)
    cur.close()

    return render_template('patient/appointments.html',
                           active_page='appointments', appointments=appts)


@patient_bp.route('/api/doctors/list')
@role_required('patient')
def get_doctors_list():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT d.id, u.full_name, d.specialization, d.consultation_fee
        FROM doctors d JOIN users u ON d.user_id=u.id
        ORDER BY u.full_name
    """)
    doctors = cur.fetchall()
    cur.close()
    return jsonify(doctors)

@patient_bp.route('/api/appointments/booked_slots')
@role_required('patient')
def get_booked_slots():
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')
    if not doctor_id or not date:
        return jsonify([])
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT appointment_time FROM appointments 
        WHERE doctor_id = %s AND appointment_date = %s 
        AND status IN ('pending', 'confirmed')
    """, (doctor_id, date))
    slots = [str(row['appointment_time']) for row in cur.fetchall()]
    cur.close()
    return jsonify(slots)

@patient_bp.route('/api/doctors/unavailability')
@role_required('patient')
def get_doctor_unavailability():
    doctor_id = request.args.get('doctor_id')
    if not doctor_id:
        return jsonify([])
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT unavailable_date FROM doctor_unavailability WHERE doctor_id = %s", (doctor_id,))
    dates = [str(row['unavailable_date']) for row in cur.fetchall()]
    cur.close()
    return jsonify(dates)


@patient_bp.route('/appointments/book', methods=['GET', 'POST'])
@role_required('patient')
def book_appointment():
    cur = mysql.connection.cursor()
    user_id = session['user_id']
    cur.execute("SELECT id FROM patients WHERE user_id=%s", (user_id,))
    patient_id = cur.fetchone()['id']

    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        date = request.form.get('appointment_date')
        time = request.form.get('appointment_time')
        reason = request.form.get('reason', '').strip()

        if not all([doctor_id, date, time, reason]):
            flash('All fields including a reason for visit are mandatory.', 'danger')
        else:
            try:
                # Robust time parsing (handle HH:mm and HH:mm:ss)
                if time and len(time) > 5:
                    selected_time = datetime.strptime(time, '%H:%M:%S').time()
                elif time:
                    selected_time = datetime.strptime(time, '%H:%M').time()
                else:
                    selected_time = None
            except ValueError:
                flash('Invalid time format.', 'danger')
                return redirect(url_for('patient.book_appointment'))

            try:
                # Ensure connection is alive and get fresh cursor
                mysql.connection.ping(True)
                cur = mysql.connection.cursor()
                # 1. Check if date is in the past
                selected_date = datetime.strptime(date, '%Y-%m-%d').date()
                if selected_date < datetime.now().date():
                    flash('You cannot book appointments for past dates.', 'danger')
                    return redirect(url_for('patient.book_appointment'))

                # 2. Block Sundays (6=Sunday)
                if selected_date.weekday() == 6:
                    flash('Appointments are not available on Sundays.', 'danger')
                    return redirect(url_for('patient.book_appointment'))

                # 3. Block Hospital Hours (08:00 - 20:00)
                if selected_time < dt_time(8, 0) or selected_time > dt_time(20, 0):
                    flash('Appointments are only available during hospital hours (08:00 AM - 08:00 PM).', 'danger')
                    return redirect(url_for('patient.book_appointment'))

                # 4. Check Doctor Unavailability (Leave)
                cur.execute("SELECT id FROM doctor_unavailability WHERE doctor_id=%s AND unavailable_date=%s", (doctor_id, date))
                if cur.fetchone():
                    flash('The selected doctor is unavailable on this date. Please choose another date.', 'danger')
                    return redirect(url_for('patient.book_appointment'))

                # 4 & 6. Comprehensive Conflict Check (Fixed exact match + 1-hour gap)
                # We exclude 'completed' and 'cancelled' status as requested.
                # Use total seconds since midnight for robust comparison
                selected_time_str = selected_time.strftime('%H:%M:%S')
                cur.execute("""
                    SELECT id FROM appointments 
                    WHERE doctor_id = %s AND appointment_date = %s 
                    AND status IN ('pending', 'confirmed')
                    AND ABS(TIME_TO_SEC(appointment_time) - TIME_TO_SEC(%s)) < 3600
                """, (doctor_id, date, selected_time_str))
                
                if cur.fetchone():
                    flash('Conflict Detected: This doctor already has an appointment within 1 hour of your selected time. Please choose a different slot.', 'danger')
                    return redirect(url_for('patient.book_appointment'))

                # 5. Check if it's in the past (time check for today)
                selected_datetime = datetime.combine(selected_date, selected_time)
                if selected_datetime < datetime.now():
                    flash('You cannot book appointments for past dates or times.', 'danger')
                    return redirect(url_for('patient.book_appointment'))

                cur.execute("""
                    INSERT INTO appointments (patient_id,doctor_id,appointment_date,appointment_time,reason,status)
                    VALUES (%s,%s,%s,%s,%s,'pending')
                """, (patient_id, doctor_id, date, time, reason))
                mysql.connection.commit()
                apt_id = cur.lastrowid

                # Enqueue in appointment queue (data structure)
                appointment_queue.enqueue({
                    'id': apt_id,
                    'patient_name': session['full_name'],
                    'appointment_date': date,
                    'status': 'pending'
                })

                flash('Appointment booked! Waiting for approval.', 'success')
                cur.close()
                return redirect(url_for('patient.appointments'))
            except Exception as e:
                print(f"Booking Error: {e}")
                flash(f'An error occurred while booking: {e}', 'danger')
                return redirect(url_for('patient.book_appointment'))

    # Get doctors list for booking form (GET request)
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT d.id, u.full_name, d.specialization, d.consultation_fee,
               d.experience_years, d.available_days, 
               d.available_time_start, d.available_time_end
        FROM doctors d JOIN users u ON d.user_id=u.id
        ORDER BY u.full_name
    """)
    doctors = cur.fetchall()
    cur.close()

    return render_template('patient/book_appointment.html',
                           active_page='book', doctors=doctors)


@patient_bp.route('/reports', methods=['GET', 'POST'])
@role_required('patient')
def reports():
    cur = mysql.connection.cursor()
    user_id = session['user_id']
    cur.execute("SELECT id FROM patients WHERE user_id=%s", (user_id,))
    patient_id = cur.fetchone()['id']

    if request.method == 'POST':
        report_type = request.form.get('report_type', '').strip()
        report_title = request.form.get('report_title', '').strip()
        findings = request.form.get('findings', '').strip()
        file = request.files.get('report_file')

        if not report_title or not report_type:
            flash('Report type and title are required.', 'danger')
        else:
            file_path = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"report_{patient_id}_{filename}"
                file_path = f"uploads/{filename}" # Use forward slashes for URL compatibility
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

            cur.execute("""
                INSERT INTO medical_reports (patient_id,report_type,report_title,file_path,findings)
                VALUES (%s,%s,%s,%s,%s)
            """, (patient_id, report_type, report_title, file_path, findings))
            mysql.connection.commit()
            flash('Report uploaded successfully!', 'success')

    cur.execute("""
        SELECT r.*, COALESCE(u.full_name,'N/A') as doctor_name
        FROM medical_reports r
        LEFT JOIN doctors d ON r.doctor_id=d.id
        LEFT JOIN users u ON d.user_id=u.id
        WHERE r.patient_id=%s
        ORDER BY r.created_at DESC
    """, (patient_id,))
    reports_list = cur.fetchall()
    cur.close()

    return render_template('patient/reports.html',
                           active_page='reports', reports=reports_list)


@patient_bp.route('/prescriptions')
@role_required('patient')
def prescriptions():
    cur = mysql.connection.cursor()
    user_id = session['user_id']
    cur.execute("SELECT id FROM patients WHERE user_id=%s", (user_id,))
    patient_id = cur.fetchone()['id']

    cur.execute("""
        SELECT pr.*, u.full_name as doctor_name, a.appointment_date, a.reason as appointment_reason
        FROM prescriptions pr
        JOIN doctors d ON pr.doctor_id=d.id
        JOIN users u ON d.user_id=u.id
        JOIN appointments a ON pr.appointment_id=a.id
        WHERE pr.patient_id=%s
        ORDER BY pr.created_at DESC
    """, (patient_id,))
    prescriptions_list = cur.fetchall()

    # Get medicines for each prescription (list data structure)
    for pres in prescriptions_list:
        cur.execute("SELECT * FROM prescription_medicines WHERE prescription_id=%s", (pres['id'],))
        pres['medicines'] = list(cur.fetchall())

    cur.close()
    return render_template('patient/prescriptions.html',
                           active_page='prescriptions', prescriptions=prescriptions_list)


@patient_bp.route('/billing')
@role_required('patient')
def billing():
    cur = mysql.connection.cursor()
    user_id = session['user_id']
    cur.execute("SELECT id FROM patients WHERE user_id=%s", (user_id,))
    patient_id = cur.fetchone()['id']

    cur.execute("""
        SELECT b.*, a.appointment_date, u.full_name as doctor_name
        FROM bills b
        LEFT JOIN appointments a ON b.appointment_id = a.id
        LEFT JOIN doctors d ON a.doctor_id = d.id
        LEFT JOIN users u ON d.user_id = u.id
        WHERE b.patient_id = %s
        ORDER BY b.created_at DESC
    """, (patient_id,))
    bills = cur.fetchall()
    
    # Get items for each bill
    for bill in bills:
        cur.execute("SELECT * FROM bill_items WHERE bill_id = %s", (bill['id'],))
        bill['bill_items'] = cur.fetchall()

    cur.close()
    return render_template('patient/billing.html', active_page='billing', bills=bills)


@patient_bp.route('/bill/pay/<int:bid>', methods=['POST'])
@role_required('patient')
def pay_bill(bid):
    cur = mysql.connection.cursor()
    # Ensure the bill belongs to the patient
    user_id = session['user_id']
    cur.execute("SELECT id FROM patients WHERE user_id=%s", (user_id,))
    patient_id = cur.fetchone()['id']

    cur.execute("SELECT id FROM bills WHERE id=%s AND patient_id=%s", (bid, patient_id))
    bill = cur.fetchone()

    if bill:
        cur.execute("""
            UPDATE bills SET payment_status='paid', payment_method='upi' 
            WHERE id=%s
        """, (bid,))
        mysql.connection.commit()
        flash('Payment successful! Thank you.', 'success')
    else:
        flash('Bill not found or access denied.', 'danger')

    cur.close()
    return redirect(url_for('patient.billing'))


@patient_bp.route('/ai-chat', methods=['POST'])
@role_required('patient')
def ai_chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'response': 'Please enter a message.'}), 400
        
    ai_response = ask_medical_bot(message)
    return jsonify({'response': ai_response})
