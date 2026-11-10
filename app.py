
import sqlite3
import os
import json

from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# ==========================================
# DATABASE CONNECTION
# ==========================================

DATABASE = os.path.join(app.root_path, 'students.db')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def initialize_database():

    conn = get_db_connection()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL
        )
    ''')

    count = conn.execute(
        'SELECT COUNT(*) FROM students'
    ).fetchone()[0]

    if count == 0:

        students = [
            ('24-00156', 'Myranie Apura', 'BSIT', 3, 'A'),
            ('24-00102', 'Mark Santos', 'BSIT', 3, 'A'),
            ('24-00103', 'John Reyes', 'BSIT', 3, 'A'),
            ('24-00104', 'Sofia Garcia', 'BSIT', 3, 'A'),
            ('24-00105', 'Daniel Flores', 'BSIT', 3, 'A')
        ]

        conn.executemany('''
            INSERT INTO students
            (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)
        ''', students)

    conn.commit()
    conn.close()


# ==========================================
# HOME PAGE
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
        "name": "Your Name",
        "program": "BSIT",
        "year": 1,
        "section": "A"
    })


# ==========================================
# ACTIVITY 6: GREETING
# ==========================================

@app.route('/hello')
def say_hello():

    name = request.args.get('name', 'Student')

    return jsonify({
        "message": f"Hello, {name}!"
    })


# ==========================================
# ACTIVITY 6: CUSTOM SCHOOL API
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

    students = conn.execute(
        'SELECT * FROM students ORDER BY id'
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# ==========================================
# ACTIVITY 7: GET ONE STUDENT
# ==========================================

@app.route('/students/<int:id>', methods=['GET'])
@app.route('/api/students/<int:id>', methods=['GET'])
def get_student_by_id(id):

    conn = get_db_connection()

    student = conn.execute(
        'SELECT * FROM students WHERE id = ?',
        (id,)
    ).fetchone()

    conn.close()

    if student is None:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify(dict(student))


# ==========================================
# ACTIVITY 7: SEARCH BY SECTION
# ==========================================

@app.route('/students/section/<section>')
def get_students_by_section(section):

    conn = get_db_connection()

    students = conn.execute(
        'SELECT * FROM students WHERE UPPER(section) = ?',
        (section.upper(),)
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# ==========================================
# ACTIVITY 8: CREATE STUDENT
# ==========================================

@app.route('/api/students', methods=['POST'])
def add_student():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "JSON data is required"
        }), 400

    required = [
        'student_id',
        'name',
        'program',
        'year',
        'section'
    ]

    if any(
        not str(data.get(field, '')).strip()
        for field in required
    ):
        return jsonify({
            "error": "All fields are required"
        }), 400

    try:
        year = int(data['year'])

        if year < 1:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Year must be a positive number"
        }), 400

    conn = get_db_connection()

    cursor = conn.execute(
        '''
        INSERT INTO students
        (student_id, name, program, year, section)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (
            data['student_id'].strip(),
            data['name'].strip(),
            data['program'].strip(),
            year,
            data['section'].strip().upper()
        )
    )

    new_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Student added successfully",
        "id": new_id
    }), 201


# ==========================================
# ACTIVITY 8: READ ONE STUDENT
# ==========================================

@app.route('/api/student-details/<int:id>', methods=['GET'])
def api_get_student(id):

    conn = get_db_connection()

    student = conn.execute(
        'SELECT * FROM students WHERE id = ?',
        (id,)
    ).fetchone()

    conn.close()

    if student is None:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify(dict(student))


# ==========================================
# ACTIVITY 8: UPDATE STUDENT
# ==========================================

@app.route('/api/students/<int:id>', methods=['PUT'])
def update_student(id):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "JSON data is required"
        }), 400

    required = [
        'student_id',
        'name',
        'program',
        'year',
        'section'
    ]

    if any(
        not str(data.get(field, '')).strip()
        for field in required
    ):
        return jsonify({
            "error": "All fields are required"
        }), 400

    try:
        year = int(data['year'])

        if year < 1:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid year"
        }), 400

    conn = get_db_connection()

    cursor = conn.execute(
        '''
        UPDATE students
        SET student_id = ?,
            name = ?,
            program = ?,
            year = ?,
            section = ?
        WHERE id = ?
        ''',
        (
            data['student_id'].strip(),
            data['name'].strip(),
            data['program'].strip(),
            year,
            data['section'].strip().upper(),
            id
        )
    )

    updated = cursor.rowcount

    conn.commit()
    conn.close()

    if updated == 0:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify({
        "message": "Student updated successfully"
    })


# ==========================================
# ACTIVITY 8: DELETE STUDENT
# ==========================================

@app.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):

    conn = get_db_connection()

    cursor = conn.execute(
        'DELETE FROM students WHERE id = ?',
        (id,)
    )

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    if deleted == 0:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify({
        "message": "Student deleted successfully"
    })


# ==========================================
# CLASSMATE API: JASMINE ROSE
# READ ONLY - DO NOT MODIFY REMOTE RECORDS
# ==========================================

CLASSMATE_API = (
    "https://jasminerose-2.onrender.com/api/students"
)


@app.route('/api/classmate/students', methods=['GET'])
def get_classmate_students():

    try:

        with urlopen(CLASSMATE_API, timeout=60) as response:

            data = json.loads(
                response.read().decode('utf-8')
            )

            if not isinstance(data, list):
                return jsonify({
                    "error": "Invalid classmate API response"
                }), 502

            return jsonify(data)

    except HTTPError as error:

        return jsonify({
            "error": "Classmate API returned an HTTP error",
            "details": str(error.code)
        }), 502

    except (URLError, TimeoutError, ValueError) as error:

        return jsonify({
            "error": "Unable to retrieve classmate records",
            "details": str(error)
        }), 502


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
        debug=True
    )
