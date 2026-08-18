"""
Doctor Routes - Dashboard, View Appointments, Add Diagnosis, Create Prescription
Uses: sort_appointments (merge sort), session dictionary
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from flask_mail import Message
from db import mysql, mail
from utils.auth import role_required
from utils.data_structures import sort_appointments

doctor_bp = Blueprint('doctor', __name__, template_folder='../templates/doctor')


@doctor_bp.route('/dashboard')
@role_required('doctor')
def dashboard():
    cur = mysql.connection.cursor()
    user_id = session['user_id']

    cur.execute("SELECT id FROM doctors WHERE user_id=%s", (user_id,))
    doc = cur.fetchone()
    if not doc:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('auth.logout'))
    doctor_id = doc['id']

    # Stats
    cur.execute("SELECT COUNT(*) as c FROM appointments WHERE doctor_id=%s AND appointment_date=CURDATE()",
                (doctor_id,))
    today_count = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) as c FROM appointments WHERE doctor_id=%s AND status='pending'",
                (doctor_id,))
    pending_count = cur.fetchone()['c']

    cur.execute("SELECT COUNT(*) as c FROM appointments WHERE doctor_id=%s AND status='completed'",
                (doctor_id,))
    completed_count = cur.fetchone()['c']

    cur.execute("SELECT COUNT(DISTINCT patient_id) as c FROM appointments WHERE doctor_id=%s",
                (doctor_id,))
    patient_count = cur.fetchone()['c']

    # Today's appointments sorted by time
    cur.execute("""
        SELECT a.*, u.full_name as patient_name, p.blood_group
        FROM appointments a
        JOIN patients p ON a.patient_id=p.id
        JOIN users u ON p.user_id=u.id
        WHERE a.doctor_id=%s AND a.appointment_date=CURDATE()
        ORDER BY a.appointment_time ASC
    """, (doctor_id,))
    today_appointments = list(cur.fetchall())

    # All recent appointments
    cur.execute("""
        SELECT a.*, u.full_name as patient_name
        FROM appointments a
        JOIN patients p ON a.patient_id=p.id
        JOIN users u ON p.user_id=u.id
        WHERE a.doctor_id=%s
        ORDER BY a.appointment_date DESC LIMIT 15
    """, (doctor_id,))
    recent = sort_appointments(list(cur.fetchall()), key='appointment_date', reverse=True)
    cur.close()

    return render_template('doctor/dashboard.html',
                           active_page='dashboard',
                           today_count=today_count,
                           pending_count=pending_count,
                           completed_count=completed_count,
                           patient_count=patient_count,
                           today_appointments=today_appointments,
                           recent_appointments=recent)


@doctor_bp.route('/appointments')
@role_required('doctor')
def appointments():
    cur = mysql.connection.cursor()
    user_id = session['user_id']

    cur.execute("SELECT id FROM doctors WHERE user_id=%s", (user_id,))
    doc = cur.fetchone()
    doctor_id = doc['id']

    cur.execute("""
        SELECT a.*, u.full_name as patient_name, p.blood_group,
               p.medical_history, p.allergies
        FROM appointments a
        JOIN patients p ON a.patient_id=p.id
        JOIN users u ON p.user_id=u.id
        WHERE a.doctor_id=%s
        ORDER BY a.appointment_date DESC
    """, (doctor_id,))
    appts = sort_appointments(list(cur.fetchall()), key='appointment_date', reverse=True)
    cur.close()

    return render_template('doctor/appointments.html',
                           active_page='appointments', appointments=appts)


@doctor_bp.route('/appointments/complete/<int:aid>')
@role_required('doctor')
def complete_appointment(aid):
    # Requirement: Doctor MUST add prescription first.
    # We will redirect them to create_prescription with a warning.
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM prescriptions WHERE appointment_id=%s", (aid,))
    if not cur.fetchone():
        flash('Protocol Violation: You MUST add a medical prescription before marking an appointment as complete.', 'warning')
        return redirect(url_for('doctor.create_prescription', aid=aid))
    
    # If prescription exists, proceed to complete (though create_prescription already handles completion)
    cur.execute("UPDATE appointments SET status='completed' WHERE id=%s", (aid,))
    mysql.connection.commit()
    cur.close()
    flash('Appointment finalized successfully.', 'success')
    return redirect(url_for('doctor.appointments'))


@doctor_bp.route('/appointments/accept/<int:aid>')
@role_required('doctor')
def accept_appointment(aid):
    cur = mysql.connection.cursor()
    
    # Get patient email and appointment details
    cur.execute("""
        SELECT u.email, u.full_name, a.appointment_date, a.appointment_time, du.full_name as doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users du ON d.user_id = du.id
        WHERE a.id = %s
    """, (aid,))
    appt_info = cur.fetchone()

    cur.execute("UPDATE appointments SET status='confirmed' WHERE id=%s", (aid,))
    
    # --- AUTO-CANCEL CONFLICTING PENDING APPOINTMENTS ---
    # When one is accepted, cancel others within the 1-hour gap for this doctor
    # Excludes 'completed' and 'cancelled' naturally since we check status = 'pending'
    cur.execute("""
        SELECT id, patient_id FROM appointments 
        WHERE doctor_id = (SELECT doctor_id FROM appointments WHERE id = %s)
        AND appointment_date = %s
        AND id != %s
        AND status = 'pending'
        AND ABS(TIME_TO_SEC(appointment_time) - TIME_TO_SEC(%s)) < 3600
    """, (aid, appt_info['appointment_date'], aid, str(appt_info['appointment_time'])))
    conflicts = cur.fetchall()

    for conf in conflicts:
        # Get patient email for notification
        cur.execute("""
            SELECT u.email, u.full_name FROM patients p 
            JOIN users u ON p.user_id = u.id WHERE p.id = %s
        """, (conf['patient_id'],))
        conf_pat = cur.fetchone()
        
        # Update status
        cur.execute("UPDATE appointments SET status='cancelled', notes='Slot no longer available (1-hour gap rule)' WHERE id=%s", (conf['id'],))
        
        # Notify
        if conf_pat:
            try:
                msg = Message('Appointment Slot No Longer Available - SmartCare HMS', recipients=[conf_pat['email']])
                msg.body = f"Hello {conf_pat['full_name']},\n\nWe regret to inform you that your appointment request has been cancelled because the selected time slot is too close to another confirmed appointment. Doctors require at least a 1-hour gap between consultations.\n\nPlease try booking a different time slot.\n\nRegards,\nSmartCare HMS Team"
                mail.send(msg)
            except Exception as e:
                print(f"Conflict Notification Error: {e}")

    mysql.connection.commit()
    
    # Send Confirmation Email for the accepted one
    if appt_info:
        try:
            msg = Message('Appointment Confirmed - SmartCare HMS', recipients=[appt_info['email']])
            msg.body = f"Hello {appt_info['full_name']},\n\nYour appointment with Dr. {appt_info['doctor_name']} on {appt_info['appointment_date']} at {appt_info['appointment_time']} has been CONFIRMED.\n\nPlease arrive 10 minutes prior to your scheduled time.\n\nRegards,\nSmartCare HMS Team"
            mail.send(msg)
        except Exception as e:
            print(f"Mail Error: {e}")

    cur.close()
    
    from utils.data_structures import appointment_queue
    appointment_queue.remove(aid)
    for conf in conflicts:
        appointment_queue.remove(conf['id'])
    
    flash('Appointment accepted. Overlapping pending requests were automatically cancelled and notified.', 'success')
    return redirect(url_for('doctor.appointments'))


@doctor_bp.route('/appointments/reject/<int:aid>')
@role_required('doctor')
def reject_appointment(aid):
    cur = mysql.connection.cursor()
    
    # Get patient email and appointment details
    cur.execute("""
        SELECT u.email, u.full_name, a.appointment_date, a.appointment_time, du.full_name as doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users u ON p.user_id = u.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users du ON d.user_id = du.id
        WHERE a.id = %s
    """, (aid,))
    appt_info = cur.fetchone()

    cur.execute("UPDATE appointments SET status='cancelled' WHERE id=%s", (aid,))
    mysql.connection.commit()
    
    # Send Rejection Email
    if appt_info:
        try:
            msg = Message('Appointment Cancelled - SmartCare HMS', recipients=[appt_info['email']])
            msg.body = f"Hello {appt_info['full_name']},\n\nWe regret to inform you that your appointment with Dr. {appt_info['doctor_name']} on {appt_info['appointment_date']} has been CANCELLED.\n\nPlease call us or book another slot via the portal.\n\nRegards,\nSmartCare HMS Team"
            mail.send(msg)
        except Exception as e:
            print(f"Mail Error: {e}")

    cur.close()
    
    from utils.data_structures import appointment_queue
    appointment_queue.remove(aid)
    
    flash('Appointment rejected and patient notified via email.', 'info')
    return redirect(url_for('doctor.appointments'))


@doctor_bp.route('/prescriptions')
@role_required('doctor')
def prescriptions():
    cur = mysql.connection.cursor()
    user_id = session['user_id']
    cur.execute("SELECT id FROM doctors WHERE user_id=%s", (user_id,))
    doc = cur.fetchone()
    doctor_id = doc['id']

    cur.execute("""
        SELECT pr.*, u.full_name as patient_name, a.appointment_date
        FROM prescriptions pr
        JOIN patients p ON pr.patient_id=p.id
        JOIN users u ON p.user_id=u.id
        JOIN appointments a ON pr.appointment_id=a.id
        WHERE pr.doctor_id=%s
        ORDER BY pr.created_at DESC
    """, (doctor_id,))
    prescriptions_list = cur.fetchall()
    cur.close()

    return render_template('doctor/prescriptions.html',
                           active_page='prescriptions', prescriptions=prescriptions_list)


@doctor_bp.route('/prescriptions/create/<int:aid>', methods=['GET', 'POST'])
@role_required('doctor')
def create_prescription(aid):
    cur = mysql.connection.cursor()
    user_id = session['user_id']
    cur.execute("SELECT id, consultation_fee FROM doctors WHERE user_id=%s", (user_id,))
    doc = cur.fetchone()
    if not doc:
        cur.close()
        flash('Doctor profile not found. Please contact admin.', 'danger')
        return redirect(url_for('auth.logout'))
    
    doctor_id = doc['id']
    consultation_fee = doc['consultation_fee']

    # Get appointment details
    cur.execute("""
        SELECT a.*, u.full_name as patient_name, p.id as pid,
               p.blood_group, p.medical_history, p.allergies
        FROM appointments a
        JOIN patients p ON a.patient_id=p.id
        JOIN users u ON p.user_id=u.id
        WHERE a.id=%s AND a.doctor_id=%s
    """, (aid, doctor_id))
    appointment = cur.fetchone()

    if not appointment:
        flash('Appointment not found.', 'danger')
        cur.close()
        return redirect(url_for('doctor.appointments'))

    # Requirement: Prescription only ON the date and AFTER the time
    now = datetime.now()
    appt_dt = appointment['appointment_date'] # date object
    appt_tm = (datetime.min + appointment['appointment_time']).time() # time object
    appt_full = datetime.combine(appt_dt, appt_tm)

    if now < appt_full:
        flash(f'Protocol Restriction: Medical prescriptions can only be issued starting from the appointment time: {appt_dt} {appt_tm}.', 'warning')
        cur.close()
        return redirect(url_for('doctor.appointments'))

    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis', '').strip()
        notes = request.form.get('notes', '').strip()
        med_names = request.form.getlist('medicine_name[]')
        med_ids = request.form.getlist('medicine_id[]')
        med_qtys = request.form.getlist('medicine_qty[]')
        med_dosages = request.form.getlist('dosage[]')
        med_frequencies = request.form.getlist('frequency[]')
        med_durations = request.form.getlist('duration[]')
        med_instructions = request.form.getlist('instructions[]')

        if not diagnosis:
            flash('Diagnosis is required.', 'danger')
        else:
            cur.execute("""
                INSERT INTO prescriptions (appointment_id,doctor_id,patient_id,diagnosis,notes)
                VALUES (%s,%s,%s,%s,%s)
            """, (aid, doctor_id, appointment['pid'], diagnosis, notes))
            pres_id = cur.connection.insert_id()
            mysql.connection.commit()

            # Insert medicines and calculate medicine total
            medicine_bill_total = 0
            bill_items = []
            
            # Add Consultation Fee to bill items
            bill_items.append({
                'desc': 'Doctor Consultation Fee',
                'type': 'consultation',
                'qty': 1,
                'price': consultation_fee
            })

            for i in range(len(med_ids)):
                mid = med_ids[i]
                qty = int(med_qtys[i]) if med_qtys[i] else 1
                if mid:
                    cur.execute("SELECT name, price FROM medicines WHERE id=%s", (mid,))
                    med_info = cur.fetchone()
                    if med_info:
                        m_name = med_info['name']
                        m_price = med_info['price']
                        medicine_bill_total += (m_price * qty)
                        
                        bill_items.append({
                            'desc': f"Medicine: {m_name}",
                            'type': 'medicine',
                            'qty': qty,
                            'price': m_price
                        })

                        cur.execute("""
                            INSERT INTO prescription_medicines
                            (prescription_id,medicine_name,dosage,frequency,duration,instructions)
                            VALUES (%s,%s,%s,%s,%s,%s)
                        """, (pres_id, m_name, med_dosages[i], med_frequencies[i], med_durations[i], med_instructions[i]))
                elif med_names[i].strip():
                    cur.execute("""
                        INSERT INTO prescription_medicines
                        (prescription_id,medicine_name,dosage,frequency,duration,instructions)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (pres_id, med_names[i], med_dosages[i], med_frequencies[i], med_durations[i], med_instructions[i]))

            # Create the Bill
            total_amount = consultation_fee + medicine_bill_total
            cur.execute("""
                INSERT INTO bills (patient_id, appointment_id, total_amount, net_amount, payment_status)
                VALUES (%s, %s, %s, %s, 'unpaid')
            """, (appointment['pid'], aid, total_amount, total_amount))
            bill_id = cur.lastrowid

            # Insert Bill Items
            for item in bill_items:
                cur.execute("""
                    INSERT INTO bill_items (bill_id, description, item_type, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (bill_id, item['desc'], item['type'], item['qty'], item['price'], item['price'] * item['qty']))

            # Mark appointment completed
            cur.execute("UPDATE appointments SET status='completed' WHERE id=%s", (aid,))
            mysql.connection.commit()
            cur.close()

            flash('Prescription created successfully!', 'success')
            return redirect(url_for('doctor.prescriptions'))

    # Get medicines list
    cur.execute("SELECT id, name, price FROM medicines WHERE stock_quantity > 0")
    medicines = cur.fetchall()
    cur.close()
    return render_template('doctor/create_prescription.html',
                           active_page='prescriptions', 
                           appointment=appointment,
                           medicines=medicines)


@doctor_bp.route('/mark-unavailable', methods=['GET', 'POST'])
@role_required('doctor')
def mark_unavailable():
    cur = mysql.connection.cursor()
    user_id = session['user_id']
    cur.execute("SELECT id FROM doctors WHERE user_id=%s", (user_id,))
    doctor_res = cur.fetchone()
    if not doctor_res:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('auth.logout'))
    doctor_id = doctor_res['id']

    if request.method == 'POST':
        date = request.form.get('unavailable_date')
        reason = request.form.get('reason', 'Doctor unavailable')

        if not date:
            flash('Date is required.', 'danger')
        else:
            # Check if informing at least 2 days ago (today + 2 days)
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
            min_date = datetime.now().date() + timedelta(days=2)
            if selected_date < min_date:
                flash('You must inform at least 2 days in advance for a leave.', 'danger')
                return redirect(url_for('doctor.mark_unavailable'))
            
            try:
                # 1. Create a Leave Request (Pending by default)
                cur.execute("""
                    INSERT INTO doctor_unavailability (doctor_id, unavailable_date, reason, status)
                    VALUES (%s, %s, %s, 'pending')
                """, (doctor_id, date, reason))
                mysql.connection.commit()

                flash(f'Leave request for {date} submitted for Admin approval.', 'success')
            except Exception as e:
                flash(f'Error or date already requested: {e}', 'danger')

    # Get list of upcoming leaves including status
    cur.execute("""
        SELECT id, unavailable_date, reason, status, created_at 
        FROM doctor_unavailability 
        WHERE doctor_id=%s AND unavailable_date >= CURDATE() 
        ORDER BY unavailable_date
    """, (doctor_id,))
    leaves = cur.fetchall()
    cur.close()

    return render_template('doctor/mark_unavailable.html', active_page='leave', leaves=leaves)


@doctor_bp.route('/patient-reports/<int:pid>')
@role_required('doctor')
def view_patient_reports(pid):
    cur = mysql.connection.cursor()
    
    # Get patient name
    cur.execute("""
        SELECT u.full_name 
        FROM patients p 
        JOIN users u ON p.user_id = u.id 
        WHERE p.id = %s
    """, (pid,))
    patient = cur.fetchone()
    
    if not patient:
        flash('Patient not found.', 'danger')
        cur.close()
        return redirect(url_for('doctor.appointments'))

    # Get reports for this patient
    cur.execute("""
        SELECT r.*, 
               CASE 
                 WHEN r.doctor_id IS NULL THEN 'Patient (Self)'
                 ELSE u.full_name 
               END as uploader_name
        FROM medical_reports r
        LEFT JOIN doctors d ON r.doctor_id = d.id
        LEFT JOIN users u ON d.user_id = u.id
        WHERE r.patient_id = %s
        ORDER BY r.created_at DESC
    """, (pid,))
    reports_list = cur.fetchall()
    cur.close()

    return render_template('doctor/patient_reports.html', 
                           active_page='appointments',
                           patient_name=patient['full_name'],
                           reports=reports_list)
