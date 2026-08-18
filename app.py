"""
Smart Care Hospital Management System - Main Flask Application
"""
import os
from flask import Flask, redirect, url_for, session, render_template
from config import Config
from db import mysql, mail
from werkzeug.security import generate_password_hash


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mysql.init_app(app)
    mail.init_app(app)

    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.doctor_routes import doctor_bp
    from routes.patient_routes import patient_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(patient_bp, url_prefix='/patient')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/dashboard-redirect')
    def dashboard_redirect():
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        role = session.get('role', 'patient')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        else:
            return redirect(url_for('patient.dashboard'))

    @app.before_request
    def ensure_admin():
        """Create default admin user on first request if not exists."""
        if getattr(app, '_admin_checked', False):
            return
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM users WHERE email=%s", ('admin@smartcare.com',))
            if not cur.fetchone():
                hashed = generate_password_hash('admin123')
                cur.execute(
                    "INSERT INTO users (full_name,email,phone,password_hash,role,is_active) VALUES(%s,%s,%s,%s,%s,%s)",
                    ('Admin User', 'admin@smartcare.com', '9999999999', hashed, 'admin', 1))
                mysql.connection.commit()
            cur.close()
            app._admin_checked = True
        except Exception as e:
            print(f"DB init: {e}")

    @app.errorhandler(404)
    def not_found(e):
        return redirect(url_for('index'))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
