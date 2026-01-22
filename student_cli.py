import psycopg2
from tabulate import tabulate
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import csv
import sys
import datetime
import os
from dotenv import load_dotenv

# ────────────────────────────────────────────────
# Load environment variables from .env file
# ────────────────────────────────────────────────
load_dotenv()

# Database Connection Settings – pulled from .env
DB_CONFIG = {
    'host':     os.getenv('DB_HOST'),
    'port':     int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME'),
    'user':     os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Safety check: make sure critical variables are set
if not all([DB_CONFIG['host'], DB_CONFIG['password']]):
    print("Error: Missing required environment variables (DB_HOST or DB_PASSWORD)")
    print("Please check your .env file and ensure it contains:")
    print("DB_HOST=your-render-host")
    print("DB_PORT=5432")
    print("DB_NAME=student_records_db")
    print("DB_USER=student_admin")
    print("DB_PASSWORD=your-password")
    sys.exit(1)

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected to database successfully!\n")
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

def run_query(conn, query, params=None, fetch=False, commit=False):
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        if fetch:
            if fetch == 'all':
                return cur.fetchall()
            elif fetch == 'one':
                return cur.fetchone()
            elif fetch == 'columns':
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return columns, rows
        if commit:
            conn.commit()
        return True
    except Exception as e:
        print(f"Query error: {e}")
        if commit:
            conn.rollback()
        return False
    finally:
        cur.close()

def validate_input(prompt, type_func, validator=None):
    while True:
        try:
            value = type_func(input(prompt).strip())
            if validator and not validator(value):
                raise ValueError
            return value
        except ValueError:
            print("Invalid input. Please try again.")

def add_student(conn):
    print("\nAdd New Student")
    first_name = input("First Name: ").strip()
    last_name = input("Last Name: ").strip()
    email = input("Email: ").strip()
    dob = validate_input("Date of Birth (YYYY-MM-DD): ", str, lambda x: len(x) == 10 and x.count('-') == 2)
    query = """
        INSERT INTO students (first_name, last_name, email, date_of_birth)
        VALUES (%s, %s, %s, %s) RETURNING student_id;
    """
    params = (first_name, last_name, email, dob)
    success = run_query(conn, query, params, commit=True)
    if success:
        print("Student added successfully!")

def enroll_student(conn):
    print("\nEnroll Student in Course")
    student_id = validate_input("Student ID: ", int, lambda x: x > 0)
    course_id = validate_input("Course ID: ", int, lambda x: x > 0)
    enrollment_date = datetime.date.today()
    # Check if student and course exist
    if not run_query(conn, "SELECT 1 FROM students WHERE student_id = %s;", (student_id,), fetch='one'):
        print("Student not found.")
        return
    if not run_query(conn, "SELECT 1 FROM courses WHERE course_id = %s;", (course_id,), fetch='one'):
        print("Course not found.")
        return
    query = """
        INSERT INTO enrollments (student_id, course_id, enrollment_date)
        VALUES (%s, %s, %s) RETURNING enrollment_id;
    """
    params = (student_id, course_id, enrollment_date)
    success = run_query(conn, query, params, commit=True)
    if success:
        print("Enrollment successful!")

def record_grade(conn):
    print("\nRecord Grade")
    enrollment_id = validate_input("Enrollment ID: ", int, lambda x: x > 0)
    assessment_type = input("Assessment Type (e.g., Quiz, Final Exam): ").strip()
    score = validate_input("Score (0-100): ", float, lambda x: 0 <= x <= 100)
    graded_at = datetime.date.today()
    # Check if enrollment exists
    if not run_query(conn, "SELECT 1 FROM enrollments WHERE enrollment_id = %s;", (enrollment_id,), fetch='one'):
        print("Enrollment not found.")
        return
    query = """
        INSERT INTO grades (enrollment_id, assessment_type, score, graded_at)
        VALUES (%s, %s, %s, %s);
    """
    params = (enrollment_id, assessment_type, score, graded_at)
    success = run_query(conn, query, params, commit=True)
    if success:
        print("Grade recorded successfully!")

def mark_attendance(conn):
    print("\nMark Attendance")
    enrollment_id = validate_input("Enrollment ID: ", int, lambda x: x > 0)
    attendance_date = validate_input("Date (YYYY-MM-DD): ", str, lambda x: len(x) == 10 and x.count('-') == 2)
    status = validate_input("Status (Present, Absent, Late, Excused): ", str, lambda x: x in ['Present', 'Absent', 'Late', 'Excused'])
    notes = input("Notes (optional): ").strip() or None
    # Check if enrollment exists
    if not run_query(conn, "SELECT 1 FROM enrollments WHERE enrollment_id = %s;", (enrollment_id,), fetch='one'):
        print("Enrollment not found.")
        return
    query = """
        INSERT INTO attendance (enrollment_id, attendance_date, status, notes)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (enrollment_id, attendance_date) DO UPDATE
        SET status = EXCLUDED.status, notes = EXCLUDED.notes;
    """
    params = (enrollment_id, attendance_date, status, notes)
    success = run_query(conn, query, params, commit=True)
    if success:
        print("Attendance marked successfully!")

def generate_report(conn):
    print("\nGenerate Report")
    print("1. Student GPA Report (CSV)")
    print("2. Student Risk Summary (PDF)")
    choice = input("Choose report type (1-2): ").strip()
    if choice == '1':
        columns, rows = run_query(conn, "SELECT * FROM student_gpa;", fetch='columns')
        if rows:
            filename = 'student_gpa_report.csv'
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)
            print(f"CSV report generated: {filename}")
        else:
            print("No data available.")
    elif choice == '2':
        columns, rows = run_query(conn, "SELECT * FROM student_risk_summary;", fetch='columns')
        if rows:
            filename = 'student_risk_summary.pdf'
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            flowables = []
            title = Paragraph("Student Risk Summary Report", styles['Title'])
            flowables.append(title)
            data = [columns] + rows
            table = Table(data)
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            table.setStyle(table_style)
            flowables.append(table)
            doc.build(flowables)
            print(f"PDF report generated: {filename}")
        else:
            print("No data available.")
    else:
        print("Invalid choice.")

def main():
    conn = connect_db()
    while True:
        print("\n" + "═"*60)
        print("          STUDENT RECORDS CLI")
        print("═"*60)
        print(" 1. Add Student")
        print(" 2. Enroll Student in Course")
        print(" 3. Record Grade")
        print(" 4. Mark Attendance")
        print(" 5. Generate Report (CSV/PDF)")
        print(" 6. Exit")
        print("─"*60)
        choice = input("Enter choice (1-6): ").strip()
        if choice == '1':
            add_student(conn)
        elif choice == '2':
            enroll_student(conn)
        elif choice == '3':
            record_grade(conn)
        elif choice == '4':
            mark_attendance(conn)
        elif choice == '5':
            generate_report(conn)
        elif choice == '6':
            print("\nGoodbye! Closing connection...")
            conn.close()
            break
        else:
            print("Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting gracefully...")