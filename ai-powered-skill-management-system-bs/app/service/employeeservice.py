import mysql.connector
from config import MYSQL_HOST, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE_NAME

class EmployeeService:
    def __init__(self):
        # Connect to MySQL using configurations from config.py
        self.db = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USERNAME,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE_NAME
        )
        self.cursor = self.db.cursor()

        # Create Employee Table if not exists
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS employee (
                            id INT PRIMARY KEY,
                            name VARCHAR(255),
                            employee_email VARCHAR(255),
                            phone_number VARCHAR(20),
                            password VARCHAR(255),
                            bio TEXT,
                            dev_interest VARCHAR(255),
                            department VARCHAR(255),
                            grade VARCHAR(10),
                            designation VARCHAR(255)
                        )""")
        self.db.commit()

    def add_employee(self, data):
        id = data['id']
        name = data['name']
        employee_email = data['employee_email']
        phone_number = data['phone_number']
        password = data['password']
        bio = data['bio']
        dev_interest = data['dev_interest']
        department = data['department']
        grade = data['grade']
        designation = data['designation']

        # Check if ID already exists
        self.cursor.execute("SELECT id FROM employee WHERE id = %s", (id,))
        existing_employee = self.cursor.fetchone()
        if existing_employee:
            return {"error": "Employee with the same ID already exists"}, 400

        # Insert data into employee table
        self.cursor.execute("""INSERT INTO employee (id, name, employee_email, phone_number, password, bio, dev_interest, department, grade, designation) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (id, name, employee_email, phone_number, password, bio, dev_interest, department, grade, designation))

        self.db.commit()
        return {"message": "Employee data added successfully"}, 201
    
    
    def get_employee_details(self, employee_id):
            self.cursor.execute("SELECT bio, dev_interest FROM employee WHERE id = %s", (employee_id,))
            employee_details = self.cursor.fetchone()
            if employee_details:
                bio, dev_interest = employee_details
                return {'bio': bio, 'dev_interest': dev_interest}
            else:
                return None