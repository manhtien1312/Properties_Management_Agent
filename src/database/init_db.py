import sqlite3
from datetime import datetime, timedelta
import random
import string

def init_database():
    """Initialize SQLite database with tables and sample data"""
    
    # Connect to database
    conn = sqlite3.connect('properties_management.db')
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute('PRAGMA foreign_keys = ON')
    
    # ===== CREATE TABLES =====
    
    # Employee table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Employee (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        department TEXT NOT NULL CHECK(department IN ('marketing', 'it')),
        role TEXT NOT NULL CHECK(role IN ('staff', 'manager')),
        manager_id INTEGER,
        hire_date DATE NOT NULL,
        tenure_months INTEGER,
        employment_status TEXT NOT NULL CHECK(employment_status IN ('active', 'resigned', 'notice_period')),
        resignation_date DATE,
        last_working_day DATE,
        exit_interview_completed BOOLEAN,
        location TEXT,
        work_mode TEXT NOT NULL CHECK(work_mode IN ('remote', 'hybrid', 'office')),
        FOREIGN KEY (manager_id) REFERENCES Employee(employee_id)
    )
    ''')
    
    # Asset table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Asset (
        asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_tag TEXT NOT NULL UNIQUE,
        serial_number TEXT NOT NULL UNIQUE,
        device_type TEXT NOT NULL CHECK(device_type IN ('laptop', 'monitor', 'phone')),
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        purchase_date DATE NOT NULL,
        purchase_value DECIMAL(10, 2) NOT NULL,
        current_value DECIMAL(10, 2) NOT NULL,
        assigned_to INTEGER,
        assignment_date DATE,
        status TEXT NOT NULL CHECK(status IN ('assigned', 'returned', 'lost', 'damaged', 'available')),
        return_date DATE,
        return_due_date DATE,
        condition TEXT NOT NULL CHECK(condition IN ('excellent', 'good', 'fair', 'poor', 'damaged')),
        condition_notes TEXT,
        location TEXT NOT NULL,
        warranty_expiry DATE NOT NULL,
        last_maintenance DATE,
        FOREIGN KEY (assigned_to) REFERENCES Employee(employee_id)
    )
    ''')
    
    # HR_Analytic table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS HR_Analytic (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        record_date DATE NOT NULL,
        performance_rating DECIMAL(3, 1) CHECK(performance_rating >= 1.0 AND performance_rating <= 5.0),
        promotion_count INTEGER,
        months_since_last_promotion INTEGER,
        salary_change_percent DECIMAL(5, 2),
        sick_days_ytd INTEGER,
        unplanned_leaves INTEGER,
        engagement_score DECIMAL(3, 1) CHECK(engagement_score >= 1.0 AND engagement_score <= 5.0),
        training_hours INTEGER,
        manager_changes INTEGER,
        department_changes INTEGER,
        overtime_hours INTEGER,
        remote_work_percent DECIMAL(5, 2),
        project_count INTEGER,
        tenure_months INTEGER,
        FOREIGN KEY (employee_id) REFERENCES Employee(employee_id)
    )
    ''')
    
    print("✓ Tables created successfully")
    
    # ===== INSERT SAMPLE DATA =====
    
    # Sample data for employees
    first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'Robert', 'Lisa', 'James', 'Mary',
                   'William', 'Patricia', 'Richard', 'Jennifer', 'Joseph', 'Linda', 'Charles', 'Barbara', 'Thomas', 'Susan']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                  'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']
    
    locations = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego']
    
    # Create employees
    managers_it = []
    managers_marketing = []
    staff_ids = []
    
    # First, create managers
    for i in range(3):  # 3 IT managers
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.lower().replace(' ', '.')}{i}@company.com"
        hire_date = datetime.now() - timedelta(days=random.randint(365, 2555))
        tenure = (datetime.now() - hire_date).days // 30
        
        cursor.execute('''
        INSERT INTO Employee 
        (full_name, email, department, role, manager_id, hire_date, tenure_months, 
         employment_status, resignation_date, last_working_day, exit_interview_completed, location, work_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, 'it', 'manager', None, hire_date.date(), tenure, 'active', None, None, False, 
              random.choice(locations), random.choice(['remote', 'hybrid', 'office'])))
        managers_it.append(cursor.lastrowid)
    
    for i in range(2):  # 2 Marketing managers
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.lower().replace(' ', '.')}{i}@company.com"
        hire_date = datetime.now() - timedelta(days=random.randint(365, 2555))
        tenure = (datetime.now() - hire_date).days // 30
        
        cursor.execute('''
        INSERT INTO Employee 
        (full_name, email, department, role, manager_id, hire_date, tenure_months, 
         employment_status, resignation_date, last_working_day, exit_interview_completed, location, work_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, 'marketing', 'manager', None, hire_date.date(), tenure, 'active', None, None, False, 
              random.choice(locations), random.choice(['remote', 'hybrid', 'office'])))
        managers_marketing.append(cursor.lastrowid)
    
    # Create staff members
    num_staff = 145
    for i in range(num_staff):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.lower().replace(' ', '.')}{i}@company.com"
        dept = random.choice(['it', 'marketing'])
        manager = random.choice(managers_it) if dept == 'it' else random.choice(managers_marketing)
        hire_date = datetime.now() - timedelta(days=random.randint(30, 2555))
        tenure = (datetime.now() - hire_date).days // 30
        
        # Some employees have resigned
        emp_status = random.choices(['active', 'resigned', 'notice_period'], weights=[0.90, 0.08, 0.02])[0]
        resignation_date = None
        last_working = None
        exit_completed = False
        
        if emp_status == 'resigned':
            resignation_date = datetime.now() - timedelta(days=random.randint(1, 365))
            last_working = resignation_date + timedelta(days=random.randint(0, 30))
            exit_completed = random.choice([True, False])
        elif emp_status == 'notice_period':
            resignation_date = datetime.now() - timedelta(days=random.randint(1, 30))
            last_working = datetime.now() + timedelta(days=random.randint(1, 60))
        
        cursor.execute('''
        INSERT INTO Employee 
        (full_name, email, department, role, manager_id, hire_date, tenure_months, 
         employment_status, resignation_date, last_working_day, exit_interview_completed, location, work_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, dept, 'staff', manager, hire_date.date(), tenure, emp_status, 
              resignation_date.date() if resignation_date else None, 
              last_working.date() if last_working else None, 
              exit_completed, random.choice(locations), random.choice(['remote', 'hybrid', 'office'])))
        staff_ids.append(cursor.lastrowid)
    
    all_employee_ids = managers_it + managers_marketing + staff_ids
    print(f"✓ Inserted {len(all_employee_ids)} employees")
    
    # Create assets
    brands_laptops = ['Dell', 'HP', 'Lenovo', 'Apple', 'ASUS']
    brands_monitors = ['Dell', 'LG', 'ASUS', 'HP', 'BenQ']
    brands_phones = ['Apple', 'Samsung', 'Google', 'Microsoft']
    
    models_laptops = ['XPS 13', 'ProBook 450', 'ThinkPad X1', 'MacBook Pro', 'VivoBook']
    models_monitors = ['U2719D', '27UP550', 'VP28UQG', 'Z27', 'BenQ EW2880U']
    models_phones = ['iPhone 13', 'Galaxy S22', 'Pixel 7', 'Surface Duo']
    
    device_types = ['laptop', 'monitor', 'phone']
    asset_counter = 1
    
    for i in range(180):  # 180 assets
        device_type = random.choice(device_types)
        
        if device_type == 'laptop':
            brand = random.choice(brands_laptops)
            model = random.choice(models_laptops)
            purchase_value = random.uniform(600, 2500)
            depreciation = random.uniform(0.5, 0.95)
        elif device_type == 'monitor':
            brand = random.choice(brands_monitors)
            model = random.choice(models_monitors)
            purchase_value = random.uniform(200, 800)
            depreciation = random.uniform(0.6, 0.95)
        else:  # phone
            brand = random.choice(brands_phones)
            model = random.choice(models_phones)
            purchase_value = random.uniform(300, 1200)
            depreciation = random.uniform(0.5, 0.85)
        
        asset_tag = f"AST-{asset_counter:06d}"
        serial_number = f"SN{random.randint(100000, 999999)}"
        purchase_date = datetime.now() - timedelta(days=random.randint(30, 1825))
        current_value = purchase_value * depreciation
        
        # Assignment logic
        assigned_to = None
        assignment_date = None
        status = random.choices(['assigned', 'returned', 'available', 'damaged', 'lost'], 
                               weights=[0.60, 0.15, 0.15, 0.05, 0.05])[0]
        
        if status == 'assigned':
            assigned_to = random.choice(all_employee_ids)
            assignment_date = datetime.now() - timedelta(days=random.randint(1, 730))
        
        return_date = None
        return_due_date = None
        if status == 'returned':
            return_date = datetime.now() - timedelta(days=random.randint(1, 365))
        elif status in ['assigned', 'damaged']:
            return_due_date = datetime.now() + timedelta(days=random.randint(1, 365))
        
        condition = random.choices(['excellent', 'good', 'fair', 'poor', 'damaged'], 
                                  weights=[0.20, 0.40, 0.25, 0.10, 0.05])[0]
        
        condition_notes = ""
        if condition in ['poor', 'damaged']:
            notes_list = ['Needs repair', 'Battery degraded', 'Screen issue', 'Keyboard malfunction', 'Hardware failure']
            condition_notes = random.choice(notes_list)
        
        warranty_expiry = purchase_date + timedelta(days=random.randint(365, 1095))
        last_maintenance = datetime.now() - timedelta(days=random.randint(30, 365))
        
        cursor.execute('''
        INSERT INTO Asset 
        (asset_tag, serial_number, device_type, brand, model, purchase_date, purchase_value, current_value,
         assigned_to, assignment_date, status, return_date, return_due_date, condition, condition_notes,
         location, warranty_expiry, last_maintenance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (asset_tag, serial_number, device_type, brand, model, purchase_date.date(), purchase_value, current_value,
              assigned_to, assignment_date.date() if assignment_date else None, status,
              return_date.date() if return_date else None,
              return_due_date.date() if return_due_date else None,
              condition, condition_notes, random.choice(locations), 
              warranty_expiry.date(), last_maintenance.date()))
        
        asset_counter += 1
    
    print(f"✓ Inserted {asset_counter - 1} assets")
    
    # Create HR Analytics records
    # Create multiple records per employee (multiple months)
    records_inserted = 0
    for employee_id in all_employee_ids:
        # Create 12 months of analytics data
        for month_offset in range(12):
            record_date = datetime.now() - timedelta(days=30 * month_offset)
            
            performance_rating = round(random.uniform(1.5, 5.0), 1)
            promotion_count = random.randint(0, 5)
            months_since_promotion = random.randint(0, 60) if promotion_count > 0 else None
            salary_change_percent = round(random.uniform(-5, 15), 2)
            sick_days_ytd = random.randint(0, 30)
            unplanned_leaves = random.randint(0, 10)
            engagement_score = round(random.uniform(1.5, 5.0), 1)
            training_hours = random.randint(0, 100)
            manager_changes = random.randint(0, 3)
            department_changes = random.randint(0, 2)
            overtime_hours = random.randint(0, 200)
            remote_work_percent = round(random.uniform(0, 100), 2)
            project_count = random.randint(1, 15)
            
            # Get employee tenure
            cursor.execute('SELECT hire_date FROM Employee WHERE employee_id = ?', (employee_id,))
            hire_date_str = cursor.fetchone()[0]
            hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d')
            tenure_months = (record_date - hire_date).days // 30
            
            cursor.execute('''
            INSERT INTO HR_Analytic 
            (employee_id, record_date, performance_rating, promotion_count, months_since_last_promotion,
             salary_change_percent, sick_days_ytd, unplanned_leaves, engagement_score, training_hours,
             manager_changes, department_changes, overtime_hours, remote_work_percent, project_count, tenure_months)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (employee_id, record_date.date(), performance_rating, promotion_count, months_since_promotion,
                  salary_change_percent, sick_days_ytd, unplanned_leaves, engagement_score, training_hours,
                  manager_changes, department_changes, overtime_hours, remote_work_percent, project_count, tenure_months))
            
            records_inserted += 1
    
    print(f"✓ Inserted {records_inserted} HR analytics records")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("\n✓ Database initialization complete!")
    print("Database file: properties_management.db")
    
    # Print summary
    conn = sqlite3.connect('properties_management.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM Employee')
    emp_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM Asset')
    asset_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM HR_Analytic')
    hr_count = cursor.fetchone()[0]
    
    print(f"\nDatabase Summary:")
    print(f"  Employees: {emp_count}")
    print(f"  Assets: {asset_count}")
    print(f"  HR Analytics Records: {hr_count}")
    
    conn.close()

if __name__ == '__main__':
    init_database()
