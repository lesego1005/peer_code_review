import psycopg2
from faker import Faker
import random

# Database connection details
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'student_records_db',
    'user': 'student_admin',
    'password': 'Money12!'  # ← change if you updated it
}

# Use default English (en_US) since en_ZA is not supported
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
    
    num_students = 350
    
    print(f"Inserting {num_students} students (with phone numbers)...")
    
    inserted_count = 0
    
    for i in range(num_students):
        first = fake.first_name()
        last = fake.last_name()
        
        # Unique-ish email
        try:
            email = fake.unique.email()
        except Exception:
            email = f"{first.lower()}.{last.lower()}{random.randint(1000,9999)}@example.com"
        
        dob = fake.date_of_birth(minimum_age=17, maximum_age=35)
        
        # Custom South African mobile phone number (realistic format)
        sa_mobile_prefixes = ['60', '61', '62', '63', '64', '65', '66', '67', '68', '69',
                              '71', '72', '73', '74', '76', '79', '81', '82', '83', '84']
        prefix = random.choice(sa_mobile_prefixes)
        
        # Three common formats
        format_choice = random.choice([
            f"0{prefix} {random.randint(100,999)} {random.randint(1000,9999)}",     # 082 123 4567
            f"+27{prefix} {random.randint(100,999)} {random.randint(1000,9999)}",   # +2782 123 4567
            f"0{prefix}{random.randint(10000000,99999999)}"                         # 0821234567
        ])
        phone = format_choice.strip()  # remove any extra spaces
        
        sql = """
        INSERT INTO students (first_name, last_name, email, date_of_birth, phone_number)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING student_id;
        """
        
        try:
            cur.execute(sql, (first, last, email, dob, phone))
            student_id = cur.fetchone()[0]
            inserted_count += 1
            
            if inserted_count % 50 == 0:
                print(f"Inserted {inserted_count} students so far...")
                
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            print(f"Skipped duplicate email: {email}")
            continue
        except Exception as e:
            print(f"Error inserting student #{i+1}: {e}")
            conn.rollback()
            break
    
    conn.commit()
    print(f"Success! Inserted {inserted_count} students total.")
    
    cur.close()
    conn.close()