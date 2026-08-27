import sqlite3
from datetime import datetime
from pathlib import Path

class SafetyDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path(__file__).parent / "safety_database.db"

        self.db_path = str(db_path)
        self.conn = None
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER,
                violation_type TEXT NOT NULL,
                risk_level TEXT CHECK(risk_level IN ('High', 'Medium', 'Low')),
                confidence REAL,
                camera_name TEXT,
                zone_name TEXT,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Acknowledged', 'Resolved')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT
            )
        ''')

        # Create detections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_name TEXT,
                source_file TEXT,
                source_type TEXT CHECK(source_type IN ('image', 'video')),
                total_persons INTEGER,
                violations_count INTEGER,
                confidence_avg REAL,
                zone_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT
            )
        ''')

        # Create camera_status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camera_status (
                camera_name TEXT PRIMARY KEY,
                status TEXT DEFAULT 'Offline' CHECK(status IN ('Online', 'Offline')),
                fps REAL,
                latency_ms REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP,
                uptime_percentage REAL DEFAULT 0.0
            )
        ''')

        # Create media_library table (NEW)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                file_type TEXT CHECK(file_type IN ('image', 'video')),
                file_size INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ============== ALERTS METHODS ==============
    def add_alert(self, detection_id, violation_type, risk_level, confidence, camera_name, zone_name, image_path):
        """Add a new alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO alerts (detection_id, violation_type, risk_level, confidence, camera_name, zone_name, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (detection_id, violation_type, risk_level, confidence, camera_name, zone_name, image_path))
            conn.commit()
            alert_id = cursor.lastrowid
            return alert_id
        finally:
            conn.close()

    def get_all_alerts(self, limit=100):
        """Get all alerts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_alerts_by_status(self, status):
        """Get alerts by status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM alerts WHERE status = ? ORDER BY created_at DESC', (status,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ============== DETECTIONS METHODS ==============
    def add_detection(self, camera_name, source_file, source_type, total_persons, violations_count, confidence_avg, zone_name, image_path):
        """Add a new detection record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO detections (camera_name, source_file, source_type, total_persons, violations_count, confidence_avg, zone_name, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (camera_name, source_file, source_type, total_persons, violations_count, confidence_avg, zone_name, image_path))
            conn.commit()
            detection_id = cursor.lastrowid
            return detection_id
        finally:
            conn.close()

    # ============== CAMERA STATUS METHODS ==============
    def update_camera_status(self, camera_name, status, fps, latency_ms):
        """Update camera status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO camera_status (camera_name, status, fps, latency_ms, last_updated, last_seen)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (camera_name, status, fps, latency_ms))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_camera_status(self):
        """Get all camera status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM camera_status')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ============== ANALYTICS METHODS ==============
    def get_hourly_violations(self):
        """Get hourly violations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT
                    strftime('%H:00', created_at) as Hour,
                    COUNT(*) as Violations
                FROM alerts
                WHERE created_at >= datetime('now', '-1 day')
                GROUP BY Hour
                ORDER BY Hour
            ''')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_daily_compliance(self):
        """Get today's compliance percentage"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT
                    COUNT(*) as total_persons,
                    SUM(violations_count) as total_violations
                FROM detections
                WHERE DATE(created_at) = DATE('now')
            ''')
            result = cursor.fetchone()
            total_persons = result['total_persons'] or 0
            total_violations = result['total_violations'] or 0

            if total_persons > 0:
                compliance = ((total_persons - total_violations) / total_persons) * 100
            else:
                compliance = 100

            return compliance
        finally:
            conn.close()

    def get_top_violations(self):
        """Get top 5 violations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT violation_type, COUNT(*) as count
                FROM alerts
                GROUP BY violation_type
                ORDER BY count DESC
                LIMIT 5
            ''')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_alerts_by_camera(self):
        """Get top cameras by violations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT camera_name, COUNT(*) as count
                FROM alerts
                GROUP BY camera_name
                ORDER BY count DESC
                LIMIT 5
            ''')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ============== MEDIA LIBRARY METHODS (NEW) ==============
    def add_media(self, filename, file_path, file_type, file_size=None, description=""):
        """Add media file to library"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO media_library (filename, file_path, file_type, file_size, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, file_path, file_type, file_size, description))
            conn.commit()
            media_id = cursor.lastrowid
            return media_id
        finally:
            conn.close()

    def get_all_media(self):
        """Get all media files"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM media_library ORDER BY uploaded_at DESC')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def delete_media(self, media_id):
        """Delete media file record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM media_library WHERE id = ?', (media_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_media_by_id(self, media_id):
        """Get media file by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM media_library WHERE id = ?', (media_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ============== UTILITY METHODS ==============
    def clear_all_data(self):
        """Clear all data from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM alerts')
            cursor.execute('DELETE FROM detections')
            cursor.execute('DELETE FROM camera_status')
            cursor.execute('DELETE FROM media_library')
            conn.commit()
        finally:
            conn.close()
