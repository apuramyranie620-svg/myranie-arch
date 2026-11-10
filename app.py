
import sqlite3
import os
import requests

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

DATABASE = os.path.join(app.root_path, 'students.db')

PARTNER_API = "https://jasminerose-2.onrender.com/api/students"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def initialize_database():
    conn = get_db_connection()

    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                name TEXT NOT NULL,
                program TEXT NOT NULL,
                year INTEGER NOT NULL,
                section TEXT NOT NULL,
                source TEXT DEFAULT 'Local'
            )
        ''')

        columns = [
            row['name']
            for row in conn.execute(
                "PRAGMA table_info(students)"
            ).fetchall()
        ]

        if 'source' not in columns:
            conn.execute(
                "ALTER TABLE students ADD COLUMN source TEXT DEFAULT 'Local'"
            )

        count = conn.execute(
            'SELECT COUNT(*) FROM students'
        ).fetchone()[0]

        if count == 0:
            students = [
                ('24-00156', 'Myranie Apura', 'BSIT', 3, 'A', 'Local'),
                ('24-00102', 'Mark Santos', 'BSIT', 3, 'A', 'Local'),
                ('24-00103', 'John Reyes', 'BSIT', 3, 'A', 'Local'),
                ('24-00104', 'Sofia Garcia', 'BSIT', 3, 'A', 'Local'),
                ('24-00105', 'Daniel Flores', 'BSIT', 3, 'A', 'Local')
            ]

            conn.executemany('''
                INSERT INTO students
                (student_id, name, program, year, section, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', students)

        conn.commit()

    finally:
        conn.close()


# ==========================================
# ACTIVITY 6: HOME PAGE
# ==========================================

@app.route('/')
def home():
    return render_template('index.html')


# ==========================================
# ACTIVITY 6: STUDENT INFORMATION
# ==========================================

@app.route('/student')
def get_student():
    return jsonify({
        "student_id": "2026-00123",
        "name": "Myranie Apura",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# ==========================================
# ACTIVITY 6: GREETING
# ==========================================

@app.route('/hello')
def say_hello():
    name = request.args.get('name', 'Student')

    return jsonify({
        "message": f"Hello, {name}! Welcome to the Student API."
    })


# ==========================================
# ACTIVITY 6: SCHOOL API
# ==========================================

@app.route('/school')
def get_school():
    return jsonify({
        "school_name": "Your School Name",
        "location": "Philippines",
        "program": "BSIT",
        "department": "Information Technology"
    })


# ==========================================
# ACTIVITY 7: GET ALL STUDENTS
# ==========================================

@app.route('/students', methods=['GET'])
@app.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db_connection()

    try:
        students = conn.execute(
            'SELECT * FROM students ORDER BY id'
        ).fetchall()

        return jsonify([dict(student) for student in students])

    finally:
        conn.close()


# ==========================================
# ACTIVITY 7: GET ONE STUDENT
# ==========================================

@app.route('/students/<int:id>', methods=['GET'])
@app.route('/api/students/<int:id>', methods=['GET'])
def get_student_by_id(id):
    conn = get_db_connection()

    try:
        student = conn.execute(
            'SELECT * FROM students WHERE id = ?',
            (id,)
        ).fetchone()

        if student is None:
            return jsonify({"error": "Student not found"}), 404

        return jsonify(dict(student))

    finally:
        conn.close()


# ==========================================
# ACTIVITY 7: SEARCH BY SECTION
# ==========================================

@app.route('/students/section/<section>', methods=['GET'])
def get_students_by_section(section):
    conn = get_db_connection()

    try:
        students = conn.execute(
            'SELECT * FROM students WHERE UPPER(section) = ?',
            (section.upper(),)
        ).fetchall()

        return jsonify([dict(student) for student in students])

    finally:
        conn.close()


# ==========================================
# ACTIVITY 8: CREATE STUDENT
# ==========================================

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON data is required"}), 400

    student_id = str(data.get('student_id') or '').strip()
    name = str(data.get('name') or '').strip()
    program = str(data.get('program') or '').strip()
    section = str(data.get('section') or '').strip().upper()

    try:
        year = int(data.get('year'))

        if year < 1:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({"error": "Year must be a positive number"}), 400

    if not all([student_id, name, program, section]):
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute('''
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            student_id,
            name,
            program,
            year,
            section,
            'Local'
        ))

        conn.commit()

        return jsonify({
            "message": "Student added successfully",
            "id": cursor.lastrowid
        }), 201

    except sqlite3.Error as error:
        conn.rollback()
        return jsonify({"error": str(error)}), 500

    finally:
        conn.close()


# ==========================================
# ACTIVITY 8: READ ONE STUDENT
# ==========================================

@app.route('/api/student-details/<int:id>', methods=['GET'])
def api_get_student(id):
    conn = get_db_connection()

    try:
        student = conn.execute(
            'SELECT * FROM students WHERE id = ?',
            (id,)
        ).fetchone()

        if student is None:
            return jsonify({"error": "Student not found"}), 404

        return jsonify(dict(student))

    finally:
        conn.close()


# ==========================================
# ACTIVITY 8: UPDATE STUDENT
# ==========================================

@app.route('/api/students/<int:id>', methods=['PUT'])
def update_student(id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON data is required"}), 400

    student_id = str(data.get('student_id') or '').strip()
    name = str(data.get('name') or '').strip()
    program = str(data.get('program') or '').strip()
    section = str(data.get('section') or '').strip().upper()

    try:
        year = int(data.get('year'))

        if year < 1:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({"error": "Invalid year"}), 400

    if not all([student_id, name, program, section]):
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute('''
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        ''', (
            student_id,
            name,
            program,
            year,
            section,
            id
        ))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        return jsonify({
            "message": "Student updated successfully"
        })

    finally:
        conn.close()


# ==========================================
# ACTIVITY 8: DELETE STUDENT
# ==========================================

@app.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            'DELETE FROM students WHERE id = ?',
            (id,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        return jsonify({
            "message": "Student deleted successfully"
        })

    finally:
        conn.close()


# ==========================================
# ACTIVITY 9: STEP 1
# RETRIEVE PARTNER RECORDS
# ==========================================

@app.route('/partner-records', methods=['GET'])
@app.route('/api/classmate/students', methods=['GET'])
def partner_records():

    try:
        response = requests.get(
            PARTNER_API,
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({
                "error": "Partner API request failed",
                "status_code": response.status_code,
                "details": response.text[:300]
            }), 502

        try:
            data = response.json()

        except ValueError:
            return jsonify({
                "error": "Partner API returned invalid JSON",
                "details": response.text[:300]
            }), 502

        # Support list or dictionary responses
        if isinstance(data, dict):
            data = data.get(
                'students',
                data.get('records', [])
            )

        if not isinstance(data, list):
            return jsonify({
                "error": "Partner API must return a list of students"
            }), 502

        return jsonify(data), 200

    except requests.RequestException as error:
        return jsonify({
            "error": "Unable to connect to partner API",
            "details": str(error)
        }), 502


# ==========================================
# ACTIVITY 9: STEP 2
# IMPORT PARTNER RECORD
# ==========================================

@app.route('/import-student', methods=['POST'])
@app.route('/save-partner-record', methods=['POST'])
def import_student():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "JSON data is required"
        }), 400

    student_id = str(data.get('student_id') or '').strip()

    name = str(
        data.get('name') or data.get('student_name') or ''
    ).strip()

    program = str(
        data.get('program') or data.get('course') or ''
    ).strip()

    section = str(data.get('section') or '').strip().upper()

    year_value = data.get('year')

    if year_value is None:
        year_value = data.get('year_level')

    try:
        year = int(year_value)

        if year < 1:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid year level"
        }), 400

    if not all([student_id, name, program, section]):
        return jsonify({
            "error": "All student fields are required"
        }), 400

    conn = get_db_connection()

    try:
        # Check for an existing student
        existing = conn.execute(
            'SELECT id FROM students WHERE student_id = ?',
            (student_id,)
        ).fetchone()

        if existing:
            return jsonify({
                "error": "This student already exists in your database"
            }), 409

        # Save partner record
        cursor = conn.execute('''
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            student_id,
            name,
            program,
            year,
            section,
            'Classmate API'
        ))

        conn.commit()

        return jsonify({
            "message": "Partner student imported successfully!",
            "id": cursor.lastrowid,
            "student_id": student_id,
            "name": name,
            "source": "Classmate API"
        }), 201

    except sqlite3.Error as error:
        conn.rollback()

        return jsonify({
            "error": "Database error",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# INITIALIZE DATABASE
# ==========================================

initialize_database()


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=False
    )
