# skillcontroller.py
from flask import Blueprint, request, jsonify
from app.service.skillservice import process_large_text_and_save_to_database
from app.service.employeeservice import EmployeeService
from app.service.skilldatasetservice import fetch_employee_details

skill_bp = Blueprint('skill_bp', __name__)
employeeservice = EmployeeService()

@skill_bp.route('/process-text/<int:employee_id>', methods=['GET'])
def process_text_and_save_to_database(employee_id):
    # Retrieve employee details by employee_id
    employee_details = employeeservice.get_employee_details(employee_id)
    if not employee_details:
        return jsonify({'error': 'Employee not found'}), 404

    # Extract bio and dev_interest from employee_details
    bio = employee_details.get('bio', '')
    dev_interest = employee_details.get('dev_interest', '')

    # Combine bio and dev_interest as input_text
    input_text = f"{bio}\n{dev_interest}"

    if not input_text:
        return jsonify({'error': 'Text parameter is required'}), 400

    # Process the large input text and save to database
    process_large_text_and_save_to_database(input_text, employee_id)
    
    # Call the function to fetch employee details
    employee_details = fetch_employee_details(employee_id)

    return jsonify({'message': 'Data processed and saved successfully'}), 200
