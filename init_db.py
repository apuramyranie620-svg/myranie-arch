
import sqlite3

conn = sqlite3.connect('students.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    name TEXT NOT NULL,
    program TEXT NOT NULL,
    year INTEGER NOT NULL,
    section TEXT NOT NULL
)
''')

cursor.execute("DELETE FROM students")

students = [
    ('24-00101', 'Angela Cruz', 'BSIT', 3, 'A'),
    ('24-00102', 'Mark Santos', 'BSIT', 3, 'A'),
    ('24-00103', 'John Reyes', 'BSIT', 3, 'A'),
    ('24-00104', 'Sofia Garcia', 'BSIT', 3, 'A'),
    ('24-00105', 'Daniel Flores', 'BSIT', 3, 'A')
]

cursor.executemany('''
INSERT INTO students (student_id, name, program, year, section)
VALUES (?, ?, ?, ?, ?)
''', students)

conn.commit()
conn.close()

print("Database created successfully.")
