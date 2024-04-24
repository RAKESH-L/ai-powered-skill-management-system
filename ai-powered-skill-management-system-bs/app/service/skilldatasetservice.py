import mysql.connector
from mysql.connector import Error
from decimal import Decimal
from datetime import datetime
from config import MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE_NAME

def create_tables_if_not_exist():
    try:
        # Establish connection to MySQL database
        db = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USERNAME,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE_NAME,
            port=MYSQL_PORT
        )

        # Create cursor to execute SQL queries
        cursor = db.cursor()

        # Create skilldataset table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skilldataset (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employeeId INT,
                createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                status ENUM('pending', 'approved', 'denied') DEFAULT 'pending'
            )
        """)

        # Create skilldatasetgroup table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skilldatasetgroup (
                id INT AUTO_INCREMENT PRIMARY KEY,
                skillsetgroup VARCHAR(255),
                percentage DECIMAL(5, 2),
                skilldatasetId INT,
                FOREIGN KEY (skilldatasetId) REFERENCES skilldataset(id)
            )
        """)

        # Create skillset table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skillset (
                id INT AUTO_INCREMENT PRIMARY KEY,
                skill VARCHAR(255),
                percentage DECIMAL(5, 2),
                skilldatasetgroupId INT,
                FOREIGN KEY (skilldatasetgroupId) REFERENCES skilldatasetgroup(id)
            )
        """)

        # Commit changes and close cursor and database connection
        db.commit()
        cursor.close()
        db.close()

    except Error as e:
        raise Exception(f"Error occurred while creating tables: {e}")

def fetch_employee_details(employee_id):
    try:
        # Create tables if not exist
        create_tables_if_not_exist()

        # Establish connection to MySQL database
        db = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USERNAME,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE_NAME,
            port=MYSQL_PORT
        )
        
        # Create cursor to execute SQL queries
        cursor = db.cursor()

        # Check if skilldataset already exists for the given employee_id
        cursor.execute("SELECT id FROM skilldataset WHERE employeeId = %s", (employee_id,))
        existing_skilldataset = cursor.fetchone()

        if existing_skilldataset:
            # If skilldataset exists, delete records from skillset table first
            skilldataset_id = existing_skilldataset[0]
            cursor.execute("DELETE FROM skillset WHERE skilldatasetgroupId IN (SELECT id FROM skilldatasetgroup WHERE skilldatasetId = %s)", (skilldataset_id,))
            # Then delete records from skilldatasetgroup table
            cursor.execute("DELETE FROM skilldatasetgroup WHERE skilldatasetId = %s", (skilldataset_id,))

            # Update updatedAt timestamp in skilldataset table
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE skilldataset SET updatedAt = %s WHERE id = %s", (current_time, skilldataset_id))

            # If status is approved or denied, change it to pending
            cursor.execute("UPDATE skilldataset SET status = 'pending' WHERE id = %s", (skilldataset_id,))

        else:
            # Insert data into skilldataset table if it doesn't exist
            insert_skilldataset_query = """
                INSERT INTO skilldataset (employeeId, status)
                VALUES (%s, 'pending')
            """
            cursor.execute(insert_skilldataset_query, (employee_id,))
            skilldataset_id = cursor.lastrowid

        # Fetch GitHub languages for the given employee_id
        github_language_query = """
            SELECT gl.language, gl.percentage
            FROM githublanguage gl
            INNER JOIN github g ON gl.github_id = g.id
            WHERE g.employeeId = %s
        """
        cursor.execute(github_language_query, (employee_id,))
        github_languages = cursor.fetchall()

        # Fetch technical skills for the given employee_id
        technical_skills_query = """
            SELECT sw.word, sw.percentage, sw.total_count_in_entity_group
            FROM skillword sw
            INNER JOIN skillgroup sg ON sw.skillgroupId = sg.id
            INNER JOIN skillmodel sm ON sg.skillModelId = sm.id
            INNER JOIN github g ON sm.employeeId = g.employeeId
            WHERE sg.type = 'TECHNICAL' AND g.employeeId = %s
        """
        cursor.execute(technical_skills_query, (employee_id,))
        technical_skills = cursor.fetchall()
        
        # Convert Decimal values to float
        github_languages = [(language, float(percentage)) for language, percentage in github_languages]
        technical_skills = [(word, float(percentage), total_count) for word, percentage, total_count in technical_skills]

        # Combine technical_skills and GitHub languages and calculate weighted average
        combined_percentages = combine_and_calculate_weighted_average(technical_skills, github_languages)

        # Insert data into skilldatasetgroup table
        insert_skilldatasetgroup_query = """
            INSERT INTO skilldatasetgroup (skillsetgroup, percentage, skilldatasetId)
            VALUES ('TECHNICAL', 100, %s)
        """
        cursor.execute(insert_skilldatasetgroup_query, (skilldataset_id,))
        skilldatasetgroup_id = cursor.lastrowid

        # Insert data into skillset table
        insert_skillset_query = """
            INSERT INTO skillset (skill, percentage, skilldatasetgroupId)
            VALUES (%s, %s, %s)
        """
        for skill, percentage in combined_percentages.items():
            cursor.execute(insert_skillset_query, (skill, percentage, skilldatasetgroup_id))

        # Commit changes and close cursor and database connection
        db.commit()
        cursor.close()
        db.close()

        # Prepare and return employee details
        employee_details = {
            'employee_id': employee_id,
            'skilldataset_id': skilldataset_id,
            'skilldatasetgroup_id': skilldatasetgroup_id
        }
        return employee_details

    except Error as e:
        raise Exception(f"Error occurred while fetching employee details: {e}")
    
def combine_and_calculate_weighted_average(technical_skills, github_languages):
    combined_percentages = {}

    # Combine technical_skills and github_languages into a single dictionary
    combined_data = {}
    for word, percentage, total_count_in_entity_group in technical_skills:
        combined_data[word] = {'technical_percentage': percentage, 'total_count_in_entity_group': total_count_in_entity_group}

    for language, percentage in github_languages:
        if language in combined_data:
            combined_data[language]['github_percentage'] = percentage
        else:
            combined_data[language] = {'github_percentage': percentage, 'technical_percentage': 0, 'total_count_in_entity_group': 0}

    # Calculate the weighted average for each word or skill or language
    for word, data in combined_data.items():
        technical_percentage = data.get('technical_percentage', 0)
        github_percentage = data.get('github_percentage', 0)
        total_count = data.get('total_count_in_entity_group', 0)

        weighted_average = ((technical_percentage * total_count) + github_percentage) / (total_count + 1)
        combined_percentages[word] = weighted_average

    return combined_percentages
