import requests
import mysql.connector
from config import MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE_NAME

class GithubService:
    def __init__(self, access_token):
        self.access_token = access_token
        
        # Connect to MySQL using configurations from config.py
        self.db = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USERNAME,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE_NAME,
            port=MYSQL_PORT
        )
        self.cursor = self.db.cursor()

        # Create Github and GithubLanguage tables if not exists
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS github (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(255),
                            employeeId INT,
                            login VARCHAR(255),
                            avatarURL VARCHAR(255),
                            bio TEXT,
                            blog VARCHAR(255),
                            createdAt VARCHAR(255),
                            email VARCHAR(255),
                            followers INT,
                            following INT,
                            publicGists INT,
                            publicRepos INT,
                            updatedAt VARCHAR(255),
                            FOREIGN KEY (employeeId) REFERENCES employee(id)
                        )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS githubLanguage (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            language VARCHAR(255),
                            percentage DECIMAL(5, 2),
                            github_id INT,
                            FOREIGN KEY (github_id) REFERENCES github(id)
                        )""")
        self.db.commit()

    def fetch_github_details(self, username):
        # Fetch user details from GitHub API
        url = f"https://api.github.com/users/{username}"
        headers = {'Authorization': f'token {self.access_token}'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            return user_data
        else:
            print(f"Failed to fetch GitHub details for user {username}. Status code: {response.status_code}")
            return None

    def store_github_data(self, username, employee_id):
        # Check if the GitHub username exists
        user_data = self.fetch_github_details(username)
        if not user_data:
            return {"error": "GitHub username does not exist"}, 400

        # Check if the employee ID already has a linked GitHub account
        sql_check_employee = "SELECT id FROM github WHERE employeeId = %s"
        self.cursor.execute(sql_check_employee, (employee_id,))
        existing_github_account = self.cursor.fetchone()
        if existing_github_account:
            return {"error": "Employee ID already has a linked GitHub account"}, 400

        # Store user details in github table
        sql = """INSERT INTO github (username, employeeId, login, avatarURL, bio, blog, createdAt, email, followers, following, publicGists, publicRepos, updatedAt)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (
            user_data.get('login', None),
            employee_id,
            user_data.get('login', None),
            user_data.get('avatar_url', None),
            user_data.get('bio', None),
            user_data.get('blog', None),
            user_data.get('created_at', None),
            user_data.get('email', None),
            user_data.get('followers', None),
            user_data.get('following', None),
            user_data.get('public_gists', None),
            user_data.get('public_repos', None),
            user_data.get('updated_at', None)
        )
        self.cursor.execute(sql, values)
        self.db.commit()

        # Get the last inserted GitHub ID
        github_id = self.cursor.lastrowid

        # Store language percentages in githubLanguage table
        languages_data = self.fetch_repository_languages(username)
        if not languages_data:
            return {"error": "Failed to fetch repository languages"}, 400

        for language, percentage in languages_data.items():
            sql = """INSERT INTO githubLanguage (language, percentage, github_id) VALUES (%s, %s, %s)"""
            values = (language, percentage, github_id)
            self.cursor.execute(sql, values)
            self.db.commit()

        return {"message": "GitHub data stored successfully"}, 201


    def fetch_repository_languages(self, username):
        # Fetch repositories data from GitHub API
        url = f"https://api.github.com/users/{username}/repos"
        headers = {'Authorization': f'token {self.access_token}'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            repos_data = response.json()
            languages_usage = {}
            for repo in repos_data:
                repo_languages_url = repo.get('languages_url')
                if repo_languages_url:
                    languages_response = requests.get(repo_languages_url, headers=headers)
                    if languages_response.status_code == 200:
                        languages_data = languages_response.json()
                        # Exclude Jupyter Notebook language
                        if 'Jupyter Notebook' in languages_data:
                            del languages_data['Jupyter Notebook']
                        for language, bytes_count in languages_data.items():
                            languages_usage[language] = languages_usage.get(language, 0) + bytes_count
            # Calculate language percentages
            total_bytes = sum(languages_usage.values())
            languages_percentages = {language: (bytes_count / total_bytes) * 100 for language, bytes_count in languages_usage.items()}
            return languages_percentages
        else:
            print(f"Failed to fetch GitHub repositories for user {username}. Status code: {response.status_code}")
            return None