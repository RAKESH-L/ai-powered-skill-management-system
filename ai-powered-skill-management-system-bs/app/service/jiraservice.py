import mysql.connector
from jira import JIRA
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_jira_issue(server_name, username, password_or_token):
    try:
        jira = JIRA(server=server_name, basic_auth=(username, password_or_token))
        issue = jira.create_issue(project='KAN', summary='New issue created', description='New issue created', issuetype={'name': 'Task'})
        return issue.key
    except Exception as e:
        logger.error(f"Failed to create Jira issue: {e}")
        return None

def create_table(cursor):
    try:
        # Create jiraboard table if not exists
        cursor.execute("""CREATE TABLE IF NOT EXISTS jiraboard (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            employeeId INT,
                            server VARCHAR(255),
                            username VARCHAR(255),
                            password_or_token VARCHAR(255),
                            assigned_person VARCHAR(255),
                            status VARCHAR(10) DEFAULT 'active',
                            UNIQUE KEY (employeeId, username)
                        )""")

        # Create jiraboardstory table if not exists
        cursor.execute("""CREATE TABLE IF NOT EXISTS jiraboardstory (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            actualdate DATE,
                            duedate DATE,
                            percentage DECIMAL(5,2),
                            priority VARCHAR(255),
                            status VARCHAR(255),
                            type VARCHAR(255),
                            name VARCHAR(255),
                            jiraboardId INT,
                            FOREIGN KEY (jiraboardId) REFERENCES jiraboard(id)
                        )""")

        # Create jiraboardsubtasks table if not exists
        cursor.execute("""CREATE TABLE IF NOT EXISTS jiraboardsubtasks (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            actualdate DATE,
                            duedate DATE,
                            percentage DECIMAL(5,2),
                            priority VARCHAR(255),
                            status VARCHAR(255),
                            type VARCHAR(255),
                            name VARCHAR(255),
                            jiraboardstoryId INT,
                            FOREIGN KEY (jiraboardstoryId) REFERENCES jiraboardstory(id)
                        )""")
        return True
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return False

def get_assigned_tasks(server_name, username, password_or_token, assigned_person, employee_id):
    try:
        # Connect to Jira instance
        jira = JIRA(server=server_name, basic_auth=(username, password_or_token))

        # Define the person to filter issues for
        assigned_person = assigned_person

        # Fetch issues assigned to the person
        jql_issues = f'project = KAN AND assignee = "{assigned_person}"'
        issues = jira.search_issues(jql_issues)

        # Fetch subtasks assigned to the person
        subtasks = []
        for issue in issues:
            subtasks.extend(jira.search_issues(f'parent="{issue.key}"'))

        # Calculate percentage completion for each task and subtask
        percentages = {}
        for issue in issues:
            transitions = jira.transitions(issue)
            total_transitions = len(transitions)
            percent = (total_transitions / len(issues)) * 100
            percentages[issue.key] = (percent, issue.fields.status.name)

        # Prepare data for API response
        data = []
        for issue in issues:
            percent, status = percentages.get(issue.key, (0, 'Unknown'))
            priority = issue.fields.priority.name
            due_date = issue.fields.duedate if hasattr(issue.fields, 'duedate') else None
            
            issue_data = {
                'name': f"{issue.key}: {issue.fields.summary}",
                'Status': status,
                'Priority': priority,
                'Due Date': str(due_date) if due_date else None,
                'Percentage': 0,
                'Type': 'Task',
                'Parent Task': None,
                'subtasks': []
            }

            # Add subtasks under each issue
            for subtask in subtasks:
                if hasattr(subtask.fields, 'parent') and subtask.fields.parent.key == issue.key:
                    subtask_percent, _ = percentages.get(subtask.key, (0, 'Unknown'))
                    subtask_priority = subtask.fields.priority.name
                    subtask_due_date = subtask.fields.duedate if hasattr(subtask.fields, 'duedate') else None
                    
                    subtask_data = {
                        'name': f"{subtask.key}: {subtask.fields.summary}",
                        'Status': subtask.fields.status.name,
                        'Priority': subtask_priority,
                        'Due Date': str(subtask_due_date) if subtask_due_date else None,
                        'Percentage': 0,
                        'Type': 'Subtask',
                        'Parent Task': issue.key
                    }
                    
                    issue_data['subtasks'].append(subtask_data)

            data.append(issue_data)

        return data
    except Exception as e:
        logger.error(f"Failed to fetch Jira board details: {e}")
        return None

def store_jira_board_details(employee_id, server_name, username, password_or_token, assigned_person):
    try:
        db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',
            database='skilldataset',
            port=3306
        )
        cursor = db.cursor()

        # Create tables if not exists
        create_table(cursor)

        # Check if the employee already exists in the jiraboard table
        cursor.execute("SELECT id, username, status FROM jiraboard WHERE employeeId = %s", (employee_id,))
        existing_employee = cursor.fetchone()

        if existing_employee:
            # Employee exists
            existing_id, existing_username, existing_status = existing_employee
            if existing_username == username:
                # Update existing records for the same employee and username
                # Make existing records inactive
                cursor.execute("UPDATE jiraboard SET status = 'inactive' WHERE id = %s", (existing_id,))
                cursor.execute("UPDATE jiraboardstory SET status = 'inactive' WHERE jiraboardId = %s", (existing_id,))
                cursor.execute("UPDATE jiraboardsubtasks SET status = 'inactive' WHERE jiraboardstoryId IN (SELECT id FROM jiraboardstory WHERE jiraboardId = %s)", (existing_id,))
                db.commit()

        # Insert or update data into jiraboard table
        cursor.execute("""INSERT INTO jiraboard (employeeId, server, username, password_or_token, assigned_person, status)
                          VALUES (%s, %s, %s, %s, %s, 'active')
                          ON DUPLICATE KEY UPDATE server = VALUES(server), password_or_token = VALUES(password_or_token), assigned_person = VALUES(assigned_person), status = 'active'""",
                          (employee_id, server_name, username, password_or_token, assigned_person))
        db.commit()

        # Fetch Jira board details and store them in the tables
        tasks_data = get_assigned_tasks(server_name, username, password_or_token, assigned_person, employee_id)
        if tasks_data:
            for task in tasks_data:
                task_name = task['name']
                task_status = task['Status']
                task_priority = task['Priority']
                task_due_date = task['Due Date']
                task_percentage = task['Percentage']
                task_type = task['Type']

                # Insert data into jiraboardstory table
                cursor.execute("""INSERT INTO jiraboardstory (actualdate, duedate, percentage, priority, status, type, name, jiraboardId)
                                  VALUES (%s, %s, %s, %s, %s, %s, %s, (SELECT id FROM jiraboard WHERE employeeId = %s))""",
                                  (datetime.now(), task_due_date, task_percentage, task_priority, task_status, task_type, task_name, employee_id))
                story_id = cursor.lastrowid
                db.commit()

                # Fetch subtasks for the current task and insert them into jiraboardsubtasks table
                for subtask in task['subtasks']:
                    subtask_name = subtask['name']
                    subtask_status = subtask['Status']
                    subtask_priority = subtask['Priority']
                    subtask_due_date = subtask['Due Date']
                    subtask_percentage = subtask['Percentage']
                    subtask_type = subtask['Type']

                    # Insert data into jiraboardsubtasks table
                    cursor.execute("""INSERT INTO jiraboardsubtasks (actualdate, duedate, percentage, priority, status, type, name, jiraboardstoryId)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                                      (datetime.now(), subtask_due_date, subtask_percentage, subtask_priority, subtask_status, subtask_type, subtask_name, story_id))
                    db.commit()

        cursor.close()
        db.close()
        return True
    except Exception as e:
        logger.error(f"Failed to fetch and store Jira board details: {e}")
        return False
