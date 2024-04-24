from urllib.parse import urlencode
from flask import Blueprint, redirect, request, jsonify
from app.service.linkedinservice import LinkedInService

linkedin_bp = Blueprint('linkedin', __name__)

@linkedin_bp.route("/profile")
def index():
    callback_url = "http://localhost:5000/callback"
    params = {
        'response_type': 'code',
        'client_id': LinkedInService.client_id,
        'redirect_uri': callback_url,
        'scope': 'openid profile email w_member_social'
    }
    authorization_url = LinkedInService.auth_url + "?" + urlencode(params)
    return redirect(authorization_url)

@linkedin_bp.route("/callback")
def callback():
    authorization_code = request.args.get('code')
    access_token = LinkedInService.get_access_token(authorization_code)
    if access_token:
        profile_data = LinkedInService.get_profile(access_token)
        if profile_data:
            employee_id = '2000080631'  # Provide the employee ID here
            LinkedInService.store_profile_data(profile_data, employee_id)  # Call the store_profile_data method
            return jsonify(profile_data)
    return "Error occurred"








# from urllib.parse import urlencode
# from flask import Blueprint, redirect, request, jsonify
# from app.service.linkedinservice import LinkedInService

# linkedin_bp = Blueprint('linkedin', __name__)

# @linkedin_bp.route("/profile")
# def index():
#     callback_url = "http://localhost:5000/callback"
#     params = {
#         'response_type': 'code',
#         'client_id': LinkedInService.client_id,
#         'redirect_uri': callback_url,
#         'scope': 'openid profile email w_member_social'
#     }
#     authorization_url = LinkedInService.auth_url + "?" + urlencode(params)
#     return redirect(authorization_url)

# @linkedin_bp.route("/callback")
# def callback():
#     authorization_code = request.args.get('code')
#     access_token = LinkedInService.get_access_token(authorization_code)
#     if access_token:
#         profile_data = LinkedInService.get_profile(access_token)
#         if profile_data:
#             employee_id = request.args.get('employee_id')  # Assuming you have employee_id in the request
#             if not employee_id:
#                 return "Error: Employee ID not provided", 400
#             if LinkedInService.store_profile_data(profile_data, employee_id):
#                 return "Profile data stored successfully", 201
#             else:
#                 return "Error storing profile data", 500
#     return "Error occurred", 500
