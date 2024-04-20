from flask import Flask, jsonify
from jira import JIRA

app = Flask(__name__)

def get_custom_field_id(jira, field_name):
    fields = jira.fields()
    for field in fields:
        if field['name'] == field_name:
            return field['id']
    return None

def get_assigned_tasks():
    # Connect to Jira instance
    jira = JIRA(server='https://rakeshlokesh2880.atlassian.net/', basic_auth=('rakeshlokesh2880@gmail.com', 'ATATT3xFfGF07Puatt46vE1-Ge0CRuIi6ksVyVrIBq3EkZdpwGUE6b0m749k19IwcfJG0d0XugOLNWQIUVn8HrrMcvXOk4_H0aisExV4ZCDswzFLUM-ulBbxRlPZdmLfnjpBBETPnJg_jBq0UmNk3C2zh4Ok4qUpFVcraAy7QyStiCMX7AoA870=FC14A710'))

    # Define the person to filter issues for
    assigned_person = 'rakeshlokesh2880@gmail.com'

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

    # Get the ID of the custom field for actual start date
    actual_start_field_id = get_custom_field_id(jira, 'Actual Start')

    # Prepare data for API response
    data = []
    for issue in issues:
        percent, status = percentages.get(issue.key, (0, 'Unknown'))
        priority = issue.fields.priority.name
        actual_start = issue.fields.customfield_10008 if actual_start_field_id else None
        due_date = issue.fields.duedate if hasattr(issue.fields, 'duedate') else None
        
        issue_data = {
            'name': f"{issue.key}: {issue.fields.summary}",
            'Status': status,
            'Priority': priority,
            'Actual Start': actual_start,
            'Due Date': str(due_date) if due_date else None,
            'Percentage': f"{percent:.2f}% completed",
            'Type': 'Task',
            'Parent Task': None,
            'subtasks': []
        }

        # Add subtasks under each issue
        for subtask in subtasks:
            if hasattr(subtask.fields, 'parent') and subtask.fields.parent.key == issue.key:
                subtask_percent, _ = percentages.get(subtask.key, (0, 'Unknown'))
                subtask_priority = subtask.fields.priority.name
                subtask_actual_start = subtask.fields.customfield_10014 if actual_start_field_id else None
                subtask_due_date = subtask.fields.duedate if hasattr(subtask.fields, 'duedate') else None
                
                subtask_data = {
                    'name': f"{subtask.key}: {subtask.fields.summary}",
                    'Status': subtask.fields.status.name,
                    'Priority': subtask_priority,
                    'Actual Start': subtask_actual_start,
                    'Due Date': str(subtask_due_date) if subtask_due_date else None,
                    'Percentage': f"{subtask_percent:.2f}% completed",
                    'Type': 'Subtask',
                    'Parent Task': issue.key
                }
                
                issue_data['subtasks'].append(subtask_data)

        data.append(issue_data)

    return data

@app.route('/', methods=['GET'])
def tasks():
    assigned_tasks = get_assigned_tasks()
    return jsonify(assigned_tasks)


if __name__ == '__main__':
    app.run(debug=True, port=8092)
