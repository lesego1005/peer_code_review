import psycopg2
from faker import Faker
import random

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'student_records_db',
    'user': 'student_admin',
    'password': 'Money12!'  # ← your password
}

fake = Faker()

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("Connected to PostgreSQL!")

# Get all enrollment_ids
cur.execute("SELECT enrollment_id FROM enrollments")
enrollment_ids = [row[0] for row in cur.fetchall()]

print(f"Found {len(enrollment_ids)} enrollments. Generating grades...")

assessment_types = ['Quiz 1', 'Midterm Exam', 'Assignment 1', 'Project', 'Final Exam', 'Quiz 2', 'Assignment 2']

inserted = 0

for enrollment_id in enrollment_ids:
    # Random 1 to 5 grades per enrollment
    num_grades = random.randint(1, 5)
    
    for _ in range(num_grades):
        assessment = random.choice(assessment_types)
        score = round(random.uniform(45, 100), 2)  # mostly decent grades
        graded_at = fake.date_between(start_date='-6m', end_date='today')
        
        sql = """
        INSERT INTO grades (enrollment_id, assessment_type, score, graded_at)
        VALUES (%s, %s, %s, %s);
        """
        
        try:
            cur.execute(sql, (enrollment_id, assessment, score, graded_at))
            inserted += 1
        except Exception as e:
            print(f"Error adding grade for enrollment {enrollment_id}: {e}")
            conn.rollback()
            break
    
    # Progress feedback
    if inserted % 2000 == 0 and inserted > 0:
        print(f"Inserted {inserted} grades so far...")

conn.commit()
print(f"Success! Inserted {inserted} grade records total.")

cur.close()
conn.close()