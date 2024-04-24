from flask import Blueprint, request, jsonify
from app.service.employeeservice import EmployeeService

employeecontroller = Blueprint('employeecontroller', __name__)

employeeservice = EmployeeService()

@employeecontroller.route('/post/employee/data', methods=['POST'])
def add_employee():
    data = request.json
    result, status_code = employeeservice.add_employee(data)
    return jsonify(result), status_code
