from flask import Blueprint, request, jsonify
from app.service.githubservice import GithubService
from config import GITHUB_ACCESS_TOKEN

github_bp = Blueprint('github', __name__)

github_service = GithubService(GITHUB_ACCESS_TOKEN)

@github_bp.route('/post/github/data', methods=['POST'])
def add_github_data():
    data = request.json
    username = data.get('username')
    employee_id = data.get('employee_id')  # Assuming you also receive the employee ID
    if not username:
        return jsonify({'error': 'GitHub username is required'}), 400

    result = github_service.store_github_data(username, employee_id)
    return jsonify(result)