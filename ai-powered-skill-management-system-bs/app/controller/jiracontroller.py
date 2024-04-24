from flask import Blueprint, jsonify, request
from app.service.jiraservice import create_jira_issue, store_jira_board_details

jira_bp = Blueprint('jira', __name__)

@jira_bp.route('/create_jira_issue', methods=['POST'])
def create_issue():
    try:
        data = request.get_json()
        server_name = data.get('server_name')
        username = data.get('username')
        password_or_token = data.get('password_or_token')
        issue_key = create_jira_issue(server_name, username, password_or_token)
        if issue_key:
            return jsonify({'issue_key': issue_key}), 200
        else:
            return jsonify({'error': 'Failed to create Jira issue'}), 500
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@jira_bp.route('/fetch_and_store_jira_board_details', methods=['POST'])
def fetch_and_store_details():
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        server_name = data.get('server_name')
        username = data.get('username')
        password_or_token = data.get('password_or_token')
        assigned_person = data.get('assigned_person')
        if store_jira_board_details(employee_id, server_name, username, password_or_token, assigned_person):
            return jsonify({'message': 'Jira board details stored successfully'}), 200
        else:
            return jsonify({'error': 'Failed to fetch and store Jira board details'}), 500
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
