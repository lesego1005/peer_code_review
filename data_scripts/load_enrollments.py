import psycopg2
from faker import Faker
import random

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'student_records_db',
    'user': 'student_admin',
    'password': 'Money12!'  # ← update if needed
}

fake = Faker('en_US')

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected to PostgreSQL!")
        return conn
    except Exception as e:
        print("Connection failed:", e)
        return None

conn = connect_db()
if conn:
    cur = conn.cursor()
    
    # First: Get all existing student_ids and course_ids
    cur.execute("SELECT student_id FROM students")
    student_ids = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT course_id FROM courses")
    course_ids = [row[0] for row in cur.fetchall()]
    
    if not student_ids or not course_ids:
        print("No students or courses found. Run load_data.py and load_courses.py first.")
        conn.close()
        exit()
    
    print(f"Found {len(student_ids)} students and {len(course_ids)} courses.")
    
    num_enrollments = 0
    min_courses_per_student = 3
    max_courses_per_student = 6
    
    print("Generating enrollments...")
    
    for student_id in student_ids:
        # Random number of courses for this student
        num_courses_for_this_student = random.randint(min_courses_per_student, max_courses_per_student)
        
        # Randomly select unique courses for this student
        selected_courses = random.sample(course_ids, min(num_courses_for_this_student, len(course_ids)))
        
        for course_id in selected_courses:
            enrollment_date = fake.date_between(start_date='-1y', end_date='today')
            status = 'Active'  # could add 'Dropped' later
            
            sql = """
            INSERT INTO enrollments (student_id, course_id, enrollment_date, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (student_id, course_id) DO NOTHING
            RETURNING enrollment_id;
            """
            
            try:
                cur.execute(sql, (student_id, course_id, enrollment_date, status))
                result = cur.fetchone()
                if result:
                    num_enrollments += 1
            except Exception as e:
                print(f"Error enrolling student {student_id} in course {course_id}: {e}")
                conn.rollback()
                break
    
        if num_enrollments % 200 == 0 and num_enrollments > 0:
            print(f"Created {num_enrollments} enrollments so far...")
    
    conn.commit()
    print(f"Success! Created {num_enrollments} enrollment records total.")
    
    cur.close()
    conn.close()