
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
# INITIALIZE DATABASE
# ==========================================

def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year TEXT NOT NULL,
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

    conn.commit()
    conn.close()


init_db()


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def student_to_dict(student):
    return {
        "id": student["id"],
        "student_id": student["student_id"],
        "name": student["name"],
        "program": student["program"],
        "year": student["year"],
        "section": student["section"],
        "source": student["source"] or "Local"
    }


def validate_student(data):
    fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in fields:
        if not str(data.get(field, "")).strip():
            return f"{field.replace('_', ' ').title()} is required."

    return None


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# GET ALL STUDENTS
# ==========================================

@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db_connection()

    records = conn.execute("""
        SELECT * FROM students
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([
        student_to_dict(student)
        for student in records
    ])


# ==========================================
# ADD STUDENT
# ==========================================

@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True) or {}

    error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, 'Local')
        """, (
            data["student_id"].strip(),
            data["name"].strip(),
            data["program"].strip(),
            data["year"].strip(),
            data["section"].strip()
        ))

        conn.commit()

        return jsonify({
            "message": "Student added successfully!"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists."
        }), 409

    finally:
        conn.close()


# ==========================================
# UPDATE STUDENT
# ==========================================

@app.route("/api/students/<int:record_id>", methods=["PUT"])
def update_student(record_id):
    data = request.get_json(silent=True) or {}

    error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

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
            data["student_id"].strip(),
            data["name"].strip(),
            data["program"].strip(),
            data["year"].strip(),
            data["section"].strip(),
            record_id
        ))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found."
            }), 404

        return jsonify({
            "message": "Student updated successfully!"
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Another student already uses that Student ID."
        }), 409

    finally:
        conn.close()


# ==========================================
# DELETE STUDENT
# ==========================================

@app.route("/api/students/<int:record_id>", methods=["DELETE"])
def delete_student(record_id):
    conn = get_db_connection()

    cursor = conn.execute(
        "DELETE FROM students WHERE id = ?",
        (record_id,)
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({
            "error": "Student not found."
        }), 404

    return jsonify({
        "message": "Student deleted successfully!"
    })


# ==========================================
# RETRIEVE PARTNER RECORDS
# ==========================================

@app.route("/partner-records", methods=["GET"])
def get_partner_records():
    try:
        response = requests.get(
            PARTNER_API,
            timeout=20
        )

        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            data = data.get(
                "students",
                data.get("records", [])
            )

        if not isinstance(data, list):
            return jsonify({
                "error": "Unexpected partner API response."
            }), 502

        return jsonify(data)

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Partner API request timed out."
        }), 504

    except requests.exceptions.RequestException as error:
        return jsonify({
            "error": "Unable to connect to Partner API.",
            "details": str(error)
        }), 502

    except ValueError:
        return jsonify({
            "error": "Partner API returned invalid JSON."
        }), 502


# ==========================================
# SAVE PARTNER RECORD
# ==========================================

@app.route("/save-partner-record", methods=["POST"])
def save_partner_record():
    data = request.get_json(silent=True) or {}

    record = {
        "student_id": str(
            data.get("student_id") or data.get("id") or ""
        ).strip(),

        "name": str(
            data.get("name") or data.get("student_name") or ""
        ).strip(),

        "program": str(
            data.get("program") or data.get("course") or ""
        ).strip(),

        "year": str(
            data.get("year") or data.get("year_level") or ""
        ).strip(),

        "section": str(
            data.get("section") or ""
        ).strip()
    }

    error = validate_student(record)

    if error:
        return jsonify({
            "error": "Incomplete partner record: " + error
        }), 400

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, 'Partner')
        """, (
            record["student_id"],
            record["name"],
            record["program"],
            record["year"],
            record["section"]
        ))

        conn.commit()

        return jsonify({
            "message": "Partner record saved successfully!"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "This Student ID already exists in your database."
        }), 409

    finally:
        conn.close()


# ==========================================
# RUN FLASK APPLICATION
# ==========================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
