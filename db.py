"""
Database Module - Smart Care Hospital Management System
Provides shared MySQL instance for all Flask route blueprints.
Uses PyMySQL (pure Python) for Vercel serverless compatibility.
"""
import pymysql
from flask import current_app, g
from flask_mail import Mail


class MySQL:
    """
    Drop-in replacement for flask-mysqldb's MySQL class using PyMySQL.
    Keeps the same `mysql.connection.cursor()` API so route files need zero changes.
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.teardown_appcontext(self._teardown)

    def _get_connection(self):
        if 'mysql_conn' not in g:
            app = current_app._get_current_object()
            g.mysql_conn = pymysql.connect(
                host=app.config.get('MYSQL_HOST', 'localhost'),
                port=int(app.config.get('MYSQL_PORT', 3306)),
                user=app.config.get('MYSQL_USER', 'root'),
                password=app.config.get('MYSQL_PASSWORD', ''),
                database=app.config.get('MYSQL_DB', ''),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=app.config.get('MYSQL_AUTOCOMMIT', True),
                connect_timeout=5,
                ssl=self._get_ssl_config(app)
            )
        else:
            # Ping to reconnect if connection was lost (handles "Server has gone away")
            try:
                g.mysql_conn.ping(reconnect=True)
            except Exception:
                g.pop('mysql_conn', None)
                return self._get_connection()
        return g.mysql_conn

    def _get_ssl_config(self, app):
        """Cloud MySQL providers (Aiven, PlanetScale, etc.) require SSL."""
        if app.config.get('MYSQL_SSL', False):
            return {'ca': app.config.get('MYSQL_SSL_CA', None)}
        return None

    @property
    def connection(self):
        return self._get_connection()

    def _teardown(self, exception):
        conn = g.pop('mysql_conn', None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


mysql = MySQL()
mail = Mail()
