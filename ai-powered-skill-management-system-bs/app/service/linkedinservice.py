import requests
import mysql.connector
from config import MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE_NAME

class LinkedInService:
    client_id = "your client id"
    client_secret = "your secret code"
    redirect_uri = "http://localhost:5000/callback"
    auth_url = "https://www.linkedin.com/oauth/v2/authorization"
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"

    @staticmethod
    def get_access_token(authorization_code):
        token_params = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'client_id': LinkedInService.client_id,
            'client_secret': LinkedInService.client_secret,
            'redirect_uri': LinkedInService.redirect_uri
        }
        response = requests.post(LinkedInService.token_url, data=token_params)
        if response.status_code == 200:
            response_data = response.json()
            if 'access_token' in response_data:
                return response_data['access_token']
        return None

    @staticmethod
    def get_profile(access_token):
        profile_url = "https://api.linkedin.com/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        profile_response = requests.get(profile_url, headers=headers)
        if profile_response.status_code == 200:
            return profile_response.json()
        return None

    @staticmethod
    def store_profile_data(profile_data, employee_id):
        try:
            db = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USERNAME,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE_NAME,
                port=MYSQL_PORT
            )
            cursor = db.cursor()
            
            # Check if the employee ID already has a linkedin account
            cursor.execute("SELECT * FROM linkedin WHERE employee_id = %s", (employee_id,))
            existing_record = cursor.fetchone()
            if existing_record:
                raise Exception("Account is already linked")

            # Create linkedin table if not exists
            cursor.execute("""CREATE TABLE IF NOT EXISTS linkedin (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                employee_id INT,
                                email VARCHAR(255),
                                emailVerified BOOLEAN,
                                givenName VARCHAR(255),
                                familyName VARCHAR(255),
                                profile_url VARCHAR(255),
                                sub VARCHAR(255),
                                name VARCHAR(255),
                                FOREIGN KEY (employee_id) REFERENCES employee(id)
                            )""")

            # Store profile data in the linkedin table
            sql = """INSERT INTO linkedin (employee_id, email, emailVerified, givenName, familyName, profile_url, sub, name)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (
                employee_id,
                profile_data.get('email', None),
                profile_data.get('email_verified', False),
                profile_data.get('given_name', None),
                profile_data.get('family_name', None),
                profile_data.get('picture', None),
                profile_data.get('sub', None),
                profile_data.get('name', None)
            )
            cursor.execute(sql, values)
            db.commit()
            cursor.close()
            db.close()
            return True
        except Exception as e:
            print(f"Error storing profile data: {e}")
            return False
