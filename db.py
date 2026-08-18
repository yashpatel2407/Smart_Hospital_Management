"""
Database Module - Smart Care Hospital Management System
Provides shared MySQL instance for all Flask route blueprints.
"""
from flask_mysqldb import MySQL
from flask_mail import Mail

mysql = MySQL()
mail = Mail()
