# 🏥 Smart Care Hospital Management System

A full-stack Hospital Management System built with **Flask** and **MySQL**, featuring role-based dashboards for Admins, Doctors, and Patients, AI-powered medical chatbot, appointment booking, prescriptions, billing, pharmacy management, and OTP-based email verification.

---

## ✨ Features

- **Role-Based Access**: Admin, Doctor, and Patient dashboards
- **Appointment Booking**: Patients can book with available doctors
- **Prescriptions & Billing**: Doctors create prescriptions; Admins manage billing
- **Pharmacy Management**: Track medicines, stock, and expiry
- **Medical Reports**: Upload and view patient reports (X-rays, lab results)
- **AI Medical Chatbot**: Powered by OpenAI for health inquiries
- **OTP Email Verification**: Secure registration with Gmail SMTP
- **Doctor Leave Management**: Doctors request leaves; Admins approve or reject

---

## 🛠️ Tech Stack

| Layer      | Technology        |
|------------|-------------------|
| Backend    | Flask (Python)    |
| Database   | MySQL / MariaDB   |
| DB Driver  | PyMySQL           |
| Frontend   | HTML5, CSS3, JS   |
| AI         | OpenAI API        |
| Email      | Flask-Mail (SMTP) |

---

## 🚀 Getting Started (Run Locally)

### Step 1: Prerequisites

- Python 3.9+
- MySQL / MariaDB (e.g. via XAMPP or standalone server)

### Step 2: Set Up the Database

Import `Schema.sql` into your MySQL server:

```bash
mysql -u root -p < Schema.sql
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

Copy `.env.example` to `.env` and fill in your database and API credentials:

```bash
cp .env.example .env
```

### Step 5: Run Application

```bash
python app.py
```

Access the application in your browser at: **[http://localhost:5000](http://localhost:5000)**

---

## 🔐 Default Admin Login

| Field    | Value                |
|----------|----------------------|
| Email    | admin@smartcare.com  |
| Password | admin123             |

---

## 📁 Project Structure

```
├── routes/
│   ├── admin_routes.py   # Admin dashboard & management
│   ├── auth_routes.py    # Login, Register, OTP verification
│   ├── doctor_routes.py  # Doctor dashboard & prescriptions
│   └── patient_routes.py # Patient dashboard & appointments
├── static/
│   ├── css/              # Stylesheets
│   ├── img/              # Images
│   ├── js/               # JavaScript files
│   └── uploads/          # Patient medical report uploads
├── templates/            # HTML templates (Jinja2)
├── utils/
│   ├── ai_helper.py      # OpenAI chatbot integration
│   ├── auth.py           # Auth decorators
│   └── data_structures.py# Custom data structure utilities
├── app.py                # Flask main application factory
├── config.py             # Application configuration
├── db.py                 # PyMySQL database connection
├── Schema.sql            # Database schema
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
└── .gitignore            # Git ignore rules
```

---

## 📄 License

Educational project for SEM3 - Full Stack Development with Python.
