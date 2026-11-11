
import sqlite3
import os

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "students.db"
)


# ==========================================
# CONNECT TO DATABASE
# ==========================================

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()


# ==========================================
# CREATE STUDENTS TABLE
# ==========================================

cursor.execute("""
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


# ==========================================
# CHECK AND ADD SOURCE COLUMN
# ==========================================

cursor.execute("PRAGMA table_info(students)")
columns = [column[1] for column in cursor.fetchall()]

if "source" not in columns:
    cursor.execute("""
        ALTER TABLE students
        ADD COLUMN source TEXT DEFAULT 'Local'
    """)

    print("Source column added successfully!")


# ==========================================
# INSERT SAMPLE STUDENT RECORDS
# ==========================================

students = [
    ("2026-00123", "Myranie Apura", "BSIT", 3, "A", "Local"),
    ("2026-00124", "Maria Santos", "BSIT", 2, "A", "Local"),
    ("2026-00125", "Pedro Reyes", "BSIT", 1, "B", "Local"),
    ("2026-00126", "Ana Garcia", "BSCS", 3, "B", "Local"),
    ("2026-00127", "Mark Lopez", "BSCS", 2, "A", "Local")
]

cursor.executemany("""
INSERT OR IGNORE INTO students
(student_id, name, program, year, section, source)
VALUES (?, ?, ?, ?, ?, ?)
""", students)


# ==========================================
# SAVE DATABASE
# ==========================================

conn.commit()


# ==========================================
# DISPLAY DATABASE RECORDS
# ==========================================

cursor.execute("SELECT * FROM students")

records = cursor.fetchall()

print("\n====================================")
print("STUDENT DATABASE INITIALIZED")
print("====================================")
print("Database:", DATABASE)
print("Total Students:", len(records))
print("------------------------------------")

for student in records:
    print(student)

print("------------------------------------")
print("Database initialization successful!")

conn.close()
