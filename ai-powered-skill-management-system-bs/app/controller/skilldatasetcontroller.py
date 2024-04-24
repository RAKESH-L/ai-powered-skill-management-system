from flask import Blueprint, request, jsonify
from app.service.skilldatasetservice import fetch_employee_details

# Create a Blueprint for the skill dataset controller
skilldataset_bp = Blueprint('skill_dataset_controller', __name__)

# Define an endpoint to fetch employee details
@skilldataset_bp.route('/fetch-employee-details/<int:employee_id>', methods=['GET'])
def get_employee_details(employee_id):
    try:
        # Call the function to fetch employee details
        employee_details = fetch_employee_details(employee_id)
        
        # Return the employee details as JSON response
        return jsonify(employee_details), 200
    
    except Exception as e:
        error_message = {"error": str(e)}
        return jsonify(error_message), 500

