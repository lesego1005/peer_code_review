import psycopg2
from faker import Faker
import random
from datetime import timedelta, date

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'student_records_db',
    'user': 'student_admin',
    'password': 'Money12!'
}

fake = Faker()

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("Connected to PostgreSQL!")

# Get all enrollment_ids
cur.execute("SELECT enrollment_id FROM enrollments")
enrollment_ids = [row[0] for row in cur.fetchall()]

print(f"Found {len(enrollment_ids)} enrollments. Generating attendance...")

inserted = 0

for enrollment_id in enrollment_ids:
    # Random number of attendance days (20–60 per enrollment)
    num_days = random.randint(20, 60)
    
    # Start date ~6 months ago, spread over time
    start_date = fake.date_between(start_date='-6m', end_date='-1m')
    
    for day_offset in range(num_days):
        attendance_date = start_date + timedelta(days=day_offset)
        status = random.choices(
            ['Present', 'Absent', 'Late', 'Excused'],
            weights=[0.75, 0.15, 0.08, 0.02]  # mostly present
        )[0]
        
        notes = fake.sentence(nb_words=3) if random.random() < 0.1 else None  # occasional note
        
        sql = """
        INSERT INTO attendance (enrollment_id, attendance_date, status, notes)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (enrollment_id, attendance_date) DO NOTHING;
        """
        
        try:
            cur.execute(sql, (enrollment_id, attendance_date, status, notes))
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Error adding attendance for enrollment {enrollment_id}: {e}")
            conn.rollback()
            break
    
    if inserted % 5000 == 0 and inserted > 0:
        print(f"Inserted {inserted} attendance records so far...")

conn.commit()
print(f"Success! Inserted {inserted} attendance records total.")

cur.close()
conn.close()