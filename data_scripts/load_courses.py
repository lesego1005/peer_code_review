import psycopg2
from faker import Faker
import random

# === Database connection ===
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'student_records_db',
    'user': 'student_admin',
    'password': 'Money12!'  # ← use your real password if changed
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
    
    # How many courses? (project says 20–30 — let's do 25)
    num_courses = 25
    
    print(f"Inserting {num_courses} courses...")
    
    # Some realistic course names / subjects (you can add more)
    course_bases = [
        "Introduction to Python Programming",
        "Data Structures and Algorithms",
        "Relational Database Design",
        "Web Development Fundamentals",
        "Machine Learning Basics",
        "Statistics for Data Science",
        "Business English Communication",
        "Financial Accounting Principles",
        "Principles of Marketing",
        "Human Resource Management",
        "Introduction to Physics",
        "General Chemistry",
        "Biology for Non-Majors",
        "Artificial Intelligence Concepts",
        "Cloud Computing Essentials",
        "Cybersecurity Fundamentals",
        "Mobile App Development",
        "Graphic Design Basics",
        "Digital Marketing Strategies",
        "Project Management Fundamentals",
        "Entrepreneurship and Innovation",
        "Software Engineering Practices",
        "Big Data Analytics",
        "Business Intelligence Tools",
        "Advanced Excel for Business"
    ]
    
    inserted = 0
    
    for i in range(num_courses):
        # Make course name varied and unique
        base = random.choice(course_bases)
        suffix = random.choice(['101', '201', '301', 'Intro', 'Advanced', 'Fundamentals'])
        course_name = f"{base} {suffix}"
        
        # Optional: add section to avoid duplicates
        course_name = f"{course_name} - Section {random.randint(1, 4)}"
        
        credits = random.randint(3, 6)
        instructor = fake.name()
        description = fake.sentence(nb_words=random.randint(10, 18))
        
        sql = """
        INSERT INTO courses (course_name, description, credits, instructor)
        VALUES (%s, %s, %s, %s)
        RETURNING course_id;
        """
        
        try:
            cur.execute(sql, (course_name, description, credits, instructor))
            course_id = cur.fetchone()[0]
            inserted += 1
            if inserted % 5 == 0:
                print(f"Inserted {inserted}: {course_name} (Credits: {credits})")
        except Exception as e:
            print(f"Error inserting course #{i+1}: {e}")
            conn.rollback()
            break
    
    conn.commit()
    print(f"Success! Inserted {inserted} courses total.")
    
    cur.close()
    conn.close()