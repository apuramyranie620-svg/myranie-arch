
import os
import sqlite3
import requests

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# ==========================================
# CONFIGURATION
# ==========================================

DATABASE = os.path.join(app.root_path, "students.db")

PARTNER_URL = "https://jasminerose-2.onrender.com"
PARTNER_API = PARTNER_URL + "/api/students"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# INITIALIZE DATABASE
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

    conn.commit()
    conn.close()


initialize_database()


# ==========================================
# NORMALIZE STUDENT DATA
# ==========================================

def normalize_student(student):

    if not isinstance(student, dict):
        return None

    return {
        "student_id": str(
            student.get("student_id")
            or student.get("id_number")
            or ""
        ).strip(),

        "name": str(
            student.get("name")
            or student.get("student_name")
            or student.get("fullname")
            or student.get("full_name")
            or ""
        ).strip(),

        "program": str(
            student.get("program")
            or student.get("course")
            or student.get("department")
            or ""
        ).strip(),

        "year": (
            student.get("year")
            or student.get("year_level")
            or student.get("yearLevel")
            or ""
        ),

        "section": str(
            student.get("section")
            or student.get("block")
            or ""
        ).strip()
    }


# ==========================================
# EXTRACT PARTNER STUDENT RECORDS
# ==========================================

def extract_student_records(data):

    if isinstance(data, list):
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    if isinstance(data, dict):

        student_keys = {
            "student_id",
            "student_name",
            "name",
            "fullname",
            "full_name"
        }

        if student_keys.intersection(data.keys()):
            return [data]

        possible_keys = [
            "students",
            "data",
            "records",
            "results",
            "items",
            "student_records"
        ]

        for key in possible_keys:

            if key in data:
                records = extract_student_records(data[key])

                if records is not None:
                    return records

        for value in data.values():

            if isinstance(value, (dict, list)):
                records = extract_student_records(value)

                if records is not None:
                    return records

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

    students = conn.execute("""
        SELECT * FROM students
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in students])


# ==========================================
# ADD STUDENT
# ==========================================

@app.route("/api/students", methods=["POST"])
def add_student():

    data = request.get_json(silent=True) or {}
    student = normalize_student(data)

    if not student or not all([
        student["student_id"],
        student["name"],
        student["program"],
        student["section"],
        str(student["year"]).isdigit()
    ]):

        return jsonify({
            "success": False,
            "message": "Complete all student information."
        }), 400

    conn = get_db_connection()

    try:

        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, 'Local')
        """, (
            student["student_id"],
            student["name"],
            student["program"],
            int(student["year"]),
            student["section"]
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student added successfully!"
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Student ID already exists."
        }), 409

    finally:
        conn.close()


# ==========================================
# UPDATE STUDENT
# ==========================================

@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):

    data = request.get_json(silent=True) or {}

    student_id_number = str(
        data.get("student_id", "")
    ).strip()

    name = str(data.get("name", "")).strip()

    program = str(data.get("program", "")).strip()

    year = str(data.get("year", "")).strip()

    section = str(data.get("section", "")).strip()

    if not all([
        student_id_number,
        name,
        program,
        year,
        section
    ]):

        return jsonify({
            "success": False,
            "message": "Please complete all student fields."
        }), 400

    if not year.isdigit():

        return jsonify({
            "success": False,
            "message": "Year must be a valid number."
        }), 400

    conn = get_db_connection()

    try:

        existing = conn.execute(
            "SELECT id FROM students WHERE id = ?",
            (student_id,)
        ).fetchone()

        if existing is None:

            return jsonify({
                "success": False,
                "message": "Student record not found."
            }), 404

        duplicate = conn.execute("""
            SELECT id FROM students
            WHERE student_id = ? AND id != ?
        """, (
            student_id_number,
            student_id
        )).fetchone()

        if duplicate:

            return jsonify({
                "success": False,
                "message": "Student ID already exists."
            }), 409

        conn.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (
            student_id_number,
            name,
            program,
            int(year),
            section,
            student_id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student updated successfully!"
        }), 200

    except sqlite3.Error as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# DELETE STUDENT
# ==========================================

@app.route("/api/students/<int:record_id>", methods=["DELETE"])
def delete_student(record_id):

    conn = get_db_connection()

    try:

        cursor = conn.execute(
            "DELETE FROM students WHERE id = ?",
            (record_id,)
        )

        conn.commit()

        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message": "Student not found."
            }), 404

        return jsonify({
            "success": True,
            "message": "Student deleted successfully!"
        })

    finally:
        conn.close()


# ==========================================
# RETRIEVE PARTNER RECORDS
# ==========================================

@app.route("/partner-records", methods=["GET"])
def partner_records():

    try:

        response = requests.get(
            PARTNER_API,
            headers={"Accept": "application/json"},
            timeout=25
        )

        if response.headers.get("cf-mitigated") == "challenge":

            return jsonify({
                "success": False,
                "error": "Partner API is protected by a Cloudflare challenge."
            }), 502

        if not response.ok:

            return jsonify({
                "success": False,
                "error": "Partner API returned HTTP "
                         + str(response.status_code)
            }), 502

        try:
            partner_data = response.json()

        except ValueError:

            return jsonify({
                "success": False,
                "error": "Partner API returned invalid JSON."
            }), 502

        records = extract_student_records(partner_data)

        if records is None:

            return jsonify({
                "success": False,
                "error": "Invalid partner API response."
            }), 502

        normalized_records = []

        for record in records:

            student = normalize_student(record)

            if student:
                normalized_records.append(student)

        return jsonify({
            "success": True,
            "message": "Partner records retrieved successfully!",
            "total": len(normalized_records),
            "records": normalized_records
        })

    except requests.exceptions.Timeout:

        return jsonify({
            "success": False,
            "error": "Partner API request timed out."
        }), 504

    except requests.exceptions.ConnectionError:

        return jsonify({
            "success": False,
            "error": "Cannot connect to the partner server."
        }), 502

    except requests.exceptions.RequestException as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 502


# ==========================================
# SAVE PARTNER RECORD TO LOCAL DATABASE
# ==========================================

@app.route("/import-student", methods=["POST"])
@app.route("/save-partner-record", methods=["POST"])
def save_partner_record():

    data = request.get_json(silent=True) or {}
    student = normalize_student(data)

    if not student or not all([
        student["student_id"],
        student["name"],
        student["program"],
        student["section"],
        str(student["year"]).isdigit()
    ]):

        return jsonify({
            "success": False,
            "message": "Invalid or incomplete student information."
        }), 400

    conn = get_db_connection()

    try:

        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, 'Classmate API')
        """, (
            student["student_id"],
            student["name"],
            student["program"],
            int(student["year"]),
            student["section"]
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Partner student saved successfully!"
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "This student already exists in your database."
        }), 409

    finally:
        conn.close()


# ==========================================
# SEND PRACTICE RECORD TO PARTNER
# ==========================================

@app.route("/send-practice-record", methods=["POST"])
def send_practice_record():

    practice_record = {
        "student_id": "EXT-001",
        "name": "Sample Exchange Record",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    }

    try:

        response = requests.post(
            PARTNER_API,
            json=practice_record,
            headers={"Accept": "application/json"},
            timeout=25
        )

        try:
            partner_response = response.json()

        except ValueError:
            partner_response = response.text[:300]

        if not response.ok:

            return jsonify({
                "success": False,
                "message": "Partner rejected the practice record.",
                "status_code": response.status_code,
                "partner_response": partner_response
            }), 502

        return jsonify({
            "success": True,
            "message": "Practice record sent successfully!",
            "partner_response": partner_response
        })

    except requests.exceptions.RequestException as error:

        return jsonify({
            "success": False,
            "message": "Unable to send practice record.",
            "details": str(error)
        }), 502


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

import os
import sqlite3
import requests

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# ==========================================
# CONFIGURATION
# ==========================================

DATABASE = os.path.join(app.root_path, "students.db")

PARTNER_URL = "https://jasminerose-2.onrender.com"
PARTNER_API = PARTNER_URL + "/api/students"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# INITIALIZE DATABASE
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

    conn.commit()
    conn.close()


initialize_database()


# ==========================================
# NORMALIZE STUDENT DATA
# ==========================================

def normalize_student(student):

    if not isinstance(student, dict):
        return None

    return {
        "student_id": str(
            student.get("student_id")
            or student.get("id_number")
            or ""
        ).strip(),

        "name": str(
            student.get("name")
            or student.get("student_name")
            or student.get("fullname")
            or student.get("full_name")
            or ""
        ).strip(),

        "program": str(
            student.get("program")
            or student.get("course")
            or student.get("department")
            or ""
        ).strip(),

        "year": (
            student.get("year")
            or student.get("year_level")
            or student.get("yearLevel")
            or ""
        ),

        "section": str(
            student.get("section")
            or student.get("block")
            or ""
        ).strip()
    }


# ==========================================
# EXTRACT PARTNER STUDENT RECORDS
# ==========================================

def extract_student_records(data):

    if isinstance(data, list):
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    if isinstance(data, dict):

        student_keys = {
            "student_id",
            "student_name",
            "name",
            "fullname",
            "full_name"
        }

        if student_keys.intersection(data.keys()):
            return [data]

        possible_keys = [
            "students",
            "data",
            "records",
            "results",
            "items",
            "student_records"
        ]

        for key in possible_keys:

            if key in data:
                records = extract_student_records(data[key])

                if records is not None:
                    return records

        for value in data.values():

            if isinstance(value, (dict, list)):
                records = extract_student_records(value)

                if records is not None:
                    return records

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

    students = conn.execute("""
        SELECT * FROM students
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in students])


# ==========================================
# ADD STUDENT
# ==========================================

@app.route("/api/students", methods=["POST"])
def add_student():

    data = request.get_json(silent=True) or {}
    student = normalize_student(data)

    if not student or not all([
        student["student_id"],
        student["name"],
        student["program"],
        student["section"],
        str(student["year"]).isdigit()
    ]):

        return jsonify({
            "success": False,
            "message": "Complete all student information."
        }), 400

    conn = get_db_connection()

    try:

        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, 'Local')
        """, (
            student["student_id"],
            student["name"],
            student["program"],
            int(student["year"]),
            student["section"]
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student added successfully!"
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Student ID already exists."
        }), 409

    finally:
        conn.close()


# ==========================================
# GET STUDENT BY ID
# ==========================================

@app.route("/api/students/<int:id>", methods=["GET"])
def api_get_student(id):

    conn = get_db_connection()

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    if student is None:

        return jsonify({
            "success": False,
            "error": "Student not found"
        }), 404

    return jsonify(dict(student))


# ==========================================
# UPDATE STUDENT
# ==========================================

@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):

    data = request.get_json(silent=True) or {}

    student_id_number = str(
        data.get("student_id", "")
    ).strip()

    name = str(data.get("name", "")).strip()

    program = str(data.get("program", "")).strip()

    year = str(data.get("year", "")).strip()

    section = str(data.get("section", "")).strip()

    if not all([
        student_id_number,
        name,
        program,
        year,
        section
    ]):

        return jsonify({
            "success": False,
            "message": "Please complete all student fields."
        }), 400

    if not year.isdigit():

        return jsonify({
            "success": False,
            "message": "Year must be a valid number."
        }), 400

    conn = get_db_connection()

    try:

        existing = conn.execute(
            "SELECT id FROM students WHERE id = ?",
            (id,)
        ).fetchone()

        if existing is None:

            return jsonify({
                "success": False,
                "message": "Student record not found."
            }), 404

        duplicate = conn.execute("""
            SELECT id FROM students
            WHERE student_id = ? AND id != ?
        """, (
            student_id_number,
            id
        )).fetchone()

        if duplicate:

            return jsonify({
                "success": False,
                "message": "Student ID already exists."
            }), 409

        conn.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (
            student_id_number,
            name,
            program,
            int(year),
            section,
            id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student updated successfully!"
        }), 200

    except sqlite3.Error as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# DELETE STUDENT
# ==========================================

@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):

    conn = get_db_connection()

    try:

        cursor = conn.execute(
            "DELETE FROM students WHERE id = ?",
            (id,)
        )

        conn.commit()

        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message": "Student not found."
            }), 404

        return jsonify({
            "success": True,
            "message": "Student deleted successfully!"
        }), 200

    finally:
        conn.close()


# ==========================================
# RETRIEVE PARTNER RECORDS
# ==========================================

@app.route("/partner-records", methods=["GET"])
def partner_records():

    try:

        response = requests.get(
            PARTNER_API,
            headers={"Accept": "application/json"},
            timeout=25
        )

        if response.headers.get("cf-mitigated") == "challenge":

            return jsonify({
                "success": False,
                "error": "Partner API is protected by a Cloudflare challenge."
            }), 502

        if not response.ok:

            return jsonify({
                "success": False,
                "error": "Partner API returned HTTP "
                         + str(response.status_code)
            }), 502

        try:
            partner_data = response.json()

        except ValueError:

            return jsonify({
                "success": False,
                "error": "Partner API returned invalid JSON."
            }), 502

        records = extract_student_records(partner_data)

        if records is None:

            return jsonify({
                "success": False,
                "error": "Invalid partner API response."
            }), 502

        normalized_records = []

        for record in records:

            student = normalize_student(record)

            if student:
                normalized_records.append(student)

        return jsonify({
            "success": True,
            "message": "Partner records retrieved successfully!",
            "total": len(normalized_records),
            "records": normalized_records
        })

    except requests.exceptions.Timeout:

        return jsonify({
            "success": False,
            "error": "Partner API request timed out."
        }), 504

    except requests.exceptions.ConnectionError:

        return jsonify({
            "success": False,
            "error": "Cannot connect to the partner server."
        }), 502

    except requests.exceptions.RequestException as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 502


# ==========================================
# SAVE PARTNER RECORD TO LOCAL DATABASE
# ==========================================

@app.route("/import-student", methods=["POST"])
@app.route("/save-partner-record", methods=["POST"])
def save_partner_record():

    data = request.get_json(silent=True) or {}
    student = normalize_student(data)

    if not student or not all([
        student["student_id"],
        student["name"],
        student["program"],
        student["section"],
        str(student["year"]).isdigit()
    ]):

        return jsonify({
            "success": False,
            "message": "Invalid or incomplete student information."
        }), 400

    conn = get_db_connection()

    try:

        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, 'Classmate API')
        """, (
            student["student_id"],
            student["name"],
            student["program"],
            int(student["year"]),
            student["section"]
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Partner student saved successfully!"
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "This student already exists in your database."
        }), 409

    finally:
        conn.close()


# ==========================================
# SEND PRACTICE RECORD TO PARTNER
# ==========================================

@app.route("/send-practice-record", methods=["POST"])
def send_practice_record():

    practice_record = {
        "student_id": "EXT-001",
        "name": "Sample Exchange Record",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    }

    try:

        response = requests.post(
            PARTNER_API,
            json=practice_record,
            headers={"Accept": "application/json"},
            timeout=25
        )

        try:
            partner_response = response.json()

        except ValueError:
            partner_response = response.text[:300]

        if not response.ok:

            return jsonify({
                "success": False,
                "message": "Partner rejected the practice record.",
                "status_code": response.status_code,
                "partner_response": partner_response
            }), 502

        return jsonify({
            "success": True,
            "message": "Practice record sent successfully!",
            "partner_response": partner_response
        })

    except requests.exceptions.RequestException as error:

        return jsonify({
            "success": False,
            "message": "Unable to send practice record.",
            "details": str(error)
        }), 502


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
