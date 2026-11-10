
import sqlite3

conn = sqlite3.connect('students.db')
cursor = conn.cursor()

# Create students table with source column
cursor.execute('''
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

# Check if source column already exists
columns = [row[1] for row in cursor.execute(
    "PRAGMA table_info(students)"
).fetchall()]

# Add source column if missing
if 'source' not in columns:
    cursor.execute('''
        ALTER TABLE students
        ADD COLUMN source TEXT DEFAULT 'Local'
    ''')

# Clear old records
cursor.execute('DELETE FROM students')

# Reset ID numbering
cursor.execute(
    "DELETE FROM sqlite_sequence WHERE name = 'students'"
)

# Sample student records
students = [
    ('24-00156', 'Myranie Apura', 'BSIT', 3, 'A', 'Local'),
    ('24-00102', 'Mark Santos', 'BSIT', 3, 'A', 'Local'),
    ('24-00103', 'John Reyes', 'BSIT', 3, 'A', 'Local'),
    ('24-00104', 'Sofia Garcia', 'BSIT', 3, 'A', 'Local'),
    ('24-00105', 'Daniel Flores', 'BSIT', 3, 'A', 'Local')
]

# Insert student records
cursor.executemany('''
INSERT INTO students
(student_id, name, program, year, section, source)
VALUES (?, ?, ?, ?, ?, ?)
''', students)

conn.commit()
conn.close()

print("Database created successfully.")
print("Source column added successfully.")
print("Five student records inserted successfully.")
