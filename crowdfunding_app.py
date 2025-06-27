import sqlite3
import re
from datetime import datetime
import getpass

def initialize_database():
    conn = sqlite3.connect('crowdfunding.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 first_name TEXT NOT NULL,
                 last_name TEXT NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 mobile_phone TEXT NOT NULL,
                 is_active INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 title TEXT NOT NULL,
                 details TEXT NOT NULL,
                 total_target REAL NOT NULL,
                 start_date TEXT NOT NULL,
                 end_date TEXT NOT NULL,
                 FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_egyptian_phone(phone):
    pattern = r'^(?:\+201|01)[0-2,5]\d{8}$'
    return re.match(pattern, phone) is not None

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def register():
    print("\n=== Registration ===")
    first_name = input("First Name: ").strip()
    last_name = input("Last Name: ").strip()
    email = input("Email: ").strip()
    if not validate_email(email):
        print("Invalid email format!")
        return
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm Password: ")
    if password != confirm_password:
        print("Passwords do not match!")
        return
    mobile_phone = input("Mobile Phone (Egyptian number): ").strip()
    if not validate_egyptian_phone(mobile_phone):
        print("Invalid Egyptian phone number!")
        return
    
    conn = sqlite3.connect('crowdfunding.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (first_name, last_name, email, password, mobile_phone, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                  (first_name, last_name, email, password, mobile_phone, 1))
        conn.commit()
        print("Registration successful! Account activated.")
    except sqlite3.IntegrityError:
        print("Email already exists!")
    conn.close()

def login():
    print("\n=== Login ===")
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")
    
    conn = sqlite3.connect('crowdfunding.db')
    c = conn.cursor()
    c.execute("SELECT id, is_active FROM users WHERE email = ? AND password = ?", (email, password))
    user = c.fetchone()
    conn.close()
    
    if user and user[1]:
        print("Login successful!")
        return user[0]
    else:
        print("Invalid credentials or account not activated!")
        return None

def create_project(user_id):
    print("\n=== Create Project ===")
    title = input("Project Title: ").strip()
    details = input("Project Details: ").strip()
    try:
        total_target = float(input("Total Target (EGP): ").strip())
    except ValueError:
        print("Invalid target amount!")
        return
    
    start_date = input("Start Date (YYYY-MM-DD): ").strip()
    end_date = input("End Date (YYYY-MM-DD): ").strip()
    
    if not (validate_date(start_date) and validate_date(end_date)):
        print("Invalid date format!")
        return
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    if start >= end or start < datetime.now():
        print("Invalid date range!")
        return
    
    conn = sqlite3.connect('crowdfunding.db')
    c = conn.cursor()
    c.execute("INSERT INTO projects (user_id, title, details, total_target, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, title, details, total_target, start_date, end_date))
    conn.commit()
    conn.close()
    print("Project created successfully!")

def view_all_projects():
    print("\n=== All Projects ===")
    conn = sqlite3.connect('crowdfunding.db')
    c = conn.cursor()
    c.execute("SELECT id, title, details, total_target, start_date, end_date, user_id FROM projects")
    projects = c.fetchall()
    conn.close()
    
    if not projects:
        print("No projects found!")
        return
    
    for project in projects:
        print(f"ID: {project[0]}")
        print(f"Title: {project[1]}")
        print(f"Details: {project[2]}")
        print(f"Target: {project[3]} EGP")
        print(f"Duration: {project[4]} to {project[5]}")
        print("-" * 30)

def edit_project(user_id):
    project_id = input("Enter Project ID to edit: ").strip()
    conn = sqlite3.connect('crowdfunding.db')
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
    project = c.fetchone()
    
    if not project:
        print("Project not found or you don't have permission!")
        conn.close()
        return
    
    print("\n=== Edit Project ===")
    title = input(f"New Title (current: {project[2]}): ").strip() or project[2]
    details = input(f"New Details (current: {project[3]}): ").strip() or project[3]
    total_target = input(f"New Target (current: {project[4]} EGP): ").strip() or str(project[4])
    
    try:
        total_target = float(total_target)
    except ValueError:
        print("Invalid target amount!")
        conn.close()
        return
    
    start_date = input(f"New Start Date (current: {project[5]}): ").strip() or project[5]
    end_date = input(f"New End Date (current: {project[6]}): ").strip() or project[6]
    
    if (start_date and not validate_date(start_date)) or (end_date and not validate_date(end_date)):
        print("Invalid date format!")
        conn.close()
        return
    
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        if start >= end or start < datetime.now():
            print("Invalid date range!")
            conn.close()
            return
    
    c.execute("UPDATE projects SET title = ?, details = ?, total_target = ?, start_date = ?, end_date = ? WHERE id = ? AND user_id = ?",
              (title, details, total_target, start_date or project[5], end_date or project[6], project_id, user_id))
    conn.commit()
    conn.close()
    print("Project updated successfully!")

def delete_project(user_id):
    project_id = input("Enter Project ID to delete: ").strip()
    conn = sqlite3.connect('crowdfunding.db')
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
    if c.rowcount > 0:
        print("Project deleted successfully!")
    else:
        print("Project not found or you don't have permission!")
    conn.commit()
    conn.close()

def search_projects_by_date():
    date = input("Enter date to search (YYYY-MM-DD): ").strip()
    if not validate_date(date):
        print("Invalid date format!")
        return
    
    conn = sqlite3.connect('crowdfunding.db')
    c = conn.cursor()
    c.execute("SELECT id, title, details, total_target, start_date, end_date FROM projects WHERE start_date <= ? AND end_date >= ?",
              (date, date))
    projects = c.fetchall()
    conn.close()
    
    if not projects:
        print("No projects found for this date!")
        return
    
    print("\n=== Projects on Date ===")
    for project in projects:
        print(f"ID: {project[0]}")
        print(f"Title: {project[1]}")
        print(f"Details: {project[2]}")
        print(f"Target: {project[3]} EGP")
        print(f"Duration: {project[4]} to {project[5]}")
        print("-" * 30)

def main():
    initialize_database()
    current_user = None
    
    while True:
        if not current_user:
            print("\n=== Crowdfunding App ===")
            print("1. Register")
            print("2. Login")
            print("3. Exit")
            choice = input("Choose an option: ").strip()
            
            if choice == '1':
                register()
            elif choice == '2':
                current_user = login()
            elif choice == '3':
                print("Goodbye!")
                break
            else:
                print("Invalid choice!")
        else:
            print("\n=== Crowdfunding App ===")
            print("1. Create Project")
            print("2. View All Projects")
            print("3. Edit Project")
            print("4. Delete Project")
            print("5. Search Projects by Date")
            print("6. Logout")
            choice = input("Choose an option: ").strip()
            
            if choice == '1':
                create_project(current_user)
            elif choice == '2':
                view_all_projects()
            elif choice == '3':
                edit_project(current_user)
            elif choice == '4':
                delete_project(current_user)
            elif choice == '5':
                search_projects_by_date()
            elif choice == '6':
                current_user = None
                print("Logged out successfully!")
            else:
                print("Invalid choice!")

if __name__ == "__main__":
    main()