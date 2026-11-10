
import os
import sqlite3
import requests

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

DATABASE = os.path.join(app.root_path, "students.db")
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL,
            source TEXT DEFAULT 'Local'
        )
    """)

    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(students)"
        ).fetchall()
    ]

    if "source" not in columns:
        conn.execute("""
            ALTER TABLE students
            ADD COLUMN source TEXT DEFAULT 'Local'
        """)

    count = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    if count == 0:
        sample_students = [
            ("24-00156", "Myranie Apura", "BSIT", 3, "A", "Local"),
            ("24-00102", "Mark Santos", "BSIT", 3, "A", "Local"),
            ("24-00103", "John Reyes", "BSIT", 3, "A", "Local"),
            ("24-00104", "Sofia Garcia", "BSIT", 3, "A", "Local"),
            ("24-00105", "Daniel Flores", "BSIT", 3, "A", "Local")
        ]

        conn.executemany("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_students)

    conn.commit()
    conn.close()


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# BASIC API ROUTES
# ==========================================

@app.route("/student", methods=["GET"])
def get_student():
    conn = get_db_connection()

    student = conn.execute("""
        SELECT * FROM students
        ORDER BY id
        LIMIT 1
    """).fetchone()

    conn.close()

    if student is None:
        return jsonify({"error": "No student found"}), 404

    return jsonify(dict(student))


@app.route("/hello", methods=["GET"])
def hello():
    name = request.args.get("name", "Student")
    return jsonify({
        "message": f"Hello, {name}! Welcome to the Student API."
    })


@app.route("/school", methods=["GET"])
def school():
    return jsonify({
        "course_code": "BSIT",
        "course_name": "Bachelor of Science in Information Technology",
        "department": "Information Technology"
    })


# ==========================================
# GET ALL STUDENTS
# ==========================================

@app.route("/students", methods=["GET"])
@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db_connection()

    students = conn.execute("""
        SELECT * FROM students
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# ==========================================
# SEARCH STUDENT INFORMATION
# ==========================================

@app.route("/api/search-students", methods=["GET"])
def search_students():
    search = request.args.get("q", "").strip()

    if not search:
        return jsonify({
            "error": "Please enter a search keyword"
        }), 400

    conn = get_db_connection()
    keyword = f"%{search}%"

    students = conn.execute("""
        SELECT * FROM students
        WHERE student_id LIKE ?
           OR name LIKE ?
           OR program LIKE ?
           OR section LIKE ?
        ORDER BY name ASC
    """, (keyword, keyword, keyword, keyword)).fetchall()

    conn.close()

    return jsonify({
        "message": "Search completed successfully",
        "total": len(students),
        "students": [dict(student) for student in students]
    })


# ==========================================
# GET STUDENT BY DATABASE ID
# ==========================================

@app.route("/students/<int:student_id>", methods=["GET"])
@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student_by_id(student_id):
    conn = get_db_connection()

    student = conn.execute("""
        SELECT * FROM students WHERE id = ?
    """, (student_id,)).fetchone()

    conn.close()

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(dict(student))


# ==========================================
# GET STUDENTS BY SECTION
# ==========================================

@app.route("/students/section/<section>", methods=["GET"])
def get_students_by_section(section):
    conn = get_db_connection()

    students = conn.execute("""
        SELECT * FROM students
        WHERE section = ?
        ORDER BY id
    """, (section,)).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# ==========================================
# POST: ADD STUDENT
# LAB ACTIVITY 8 AND STEP 8
# ==========================================

@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid or missing JSON data"
        }), 400

    student_id = str(data.get("student_id", "")).strip()
    name = str(
        data.get("name", data.get("student_name", ""))
    ).strip()
    program = str(
        data.get("program", data.get("course", ""))
    ).strip()
    year = data.get("year", data.get("year_level"))
    section = str(data.get("section", "")).strip()

    # Step 8: Identify externally received records
    source = str(data.get("source", "External API")).strip()

    if not all([student_id, name, program, section]) or year is None:
        return jsonify({
            "error": "All student fields are required"
        }), 400

    try:
        year = int(year)
        if year < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "error": "Year must be a valid positive number"
        }), 400

    if not source:
        source = "External API"

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_id, name, program, year, section, source
        ))

        conn.commit()

        return jsonify({
            "message": "Student record added successfully",
            "student": {
                "student_id": student_id,
                "name": name,
                "program": program,
                "year": year,
                "section": section,
                "source": source
            }
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists"
        }), 409

    finally:
        conn.close()


# ==========================================
# GET STUDENT DETAILS
# ==========================================

@app.route("/api/student-details/<int:student_id>", methods=["GET"])
def student_details(student_id):
    conn = get_db_connection()

    student = conn.execute("""
        SELECT * FROM students WHERE id = ?
    """, (student_id,)).fetchone()

    conn.close()

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(dict(student))


# ==========================================
# UPDATE STUDENT
# ==========================================

@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON data"}), 400

    student_id_value = str(data.get("student_id", "")).strip()
    name = str(data.get("name", "")).strip()
    program = str(data.get("program", "")).strip()
    year = data.get("year")
    section = str(data.get("section", "")).strip()

    if not all([student_id_value, name, program, section]) or year is None:
        return jsonify({
            "error": "All student fields are required"
        }), 400

    try:
        year = int(year)
        if year < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid year"}), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (
            student_id_value,
            name,
            program,
            year,
            section,
            student_id
        ))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        return jsonify({
            "message": "Student updated successfully"
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists"
        }), 409

    finally:
        conn.close()


# ==========================================
# DELETE STUDENT
# ==========================================

@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    conn = get_db_connection()

    cursor = conn.execute("""
        DELETE FROM students WHERE id = ?
    """, (student_id,))

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Student not found"}), 404

    return jsonify({
        "message": "Student deleted successfully"
    })


# ==========================================
# GET PARTNER RECORDS
# ==========================================

@app.route("/partner-records", methods=["GET"])
@app.route("/api/classmate/students", methods=["GET"])
def get_partner_records():
    try:
        response = requests.get(PARTNER_API, timeout=20)
        response.raise_for_status()

        partner_data = response.json()

        if isinstance(partner_data, dict):
            partner_data = partner_data.get("students", [])

        if not isinstance(partner_data, list):
            return jsonify({
                "error": "Partner API did not return a student list"
            }), 502

        return jsonify(partner_data)

    except requests.exceptions.RequestException as error:
        return jsonify({
            "error": "Unable to connect to partner API",
            "details": str(error)
        }), 502

    except ValueError:
        return jsonify({
            "error": "Partner API returned invalid JSON"
        }), 502


# ==========================================
# SAVE PARTNER RECORD TO LOCAL DATABASE
# ==========================================

@app.route("/save-partner-record", methods=["POST"])
@app.route("/import-student", methods=["POST"])
def save_partner_record():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON data"}), 400

    student_id = str(data.get("student_id", "")).strip()
    name = str(
        data.get("name", data.get("student_name", ""))
    ).strip()
    program = str(
        data.get("program", data.get("course", ""))
    ).strip()
    year = data.get("year", data.get("year_level"))
    section = str(data.get("section", "")).strip()

    if not all([student_id, name, program, section]) or year is None:
        return jsonify({
            "error": "All student fields are required"
        }), 400

    try:
        year = int(year)
        if year < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid year"}), 400

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            name,
            program,
            year,
            section,
            "Classmate API"
        ))

        conn.commit()

        return jsonify({
            "message": "Partner record saved successfully",
            "source": "Classmate API"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists in your database"
        }), 409

    finally:
        conn.close()


# ==========================================
# START APPLICATION
# ==========================================

initialize_database()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
