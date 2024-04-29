import io
import time
import re
import base64
import mysql.connector 
from mysql.connector import Error
from flask import Flask, jsonify, request
from flask_cors import CORS
from azure.cognitiveservices.speech import SpeechConfig, AudioConfig, SpeechSynthesizer
from openai import AzureOpenAI
from config import YOUR_SPEECH_KEY, YOUR_SPEECH_REGION, YOUR_OPENAI_API_KEY, YOUR_OPENAI_ENDPOINT, YOUR_SYSTEM_MESSAGE, MYSQL_HOST, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE_NAME

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes of your Flask app

# Initialize Azure Cognitive Services for Speech
speech_key = YOUR_SPEECH_KEY
speech_region = YOUR_SPEECH_REGION
speech_config = SpeechConfig(subscription=speech_key, region=speech_region)
audio_config = AudioConfig(use_default_microphone=True)
speech_synthesizer = SpeechSynthesizer(speech_config=speech_config)

# Initialize OpenAI model
api_key = YOUR_OPENAI_API_KEY
endpoint = YOUR_OPENAI_ENDPOINT
client = AzureOpenAI(api_key=api_key, api_version="2024-02-15-preview", azure_endpoint=endpoint)

# Initialize MySQL connection
mysql_host = MYSQL_HOST
mysql_user = MYSQL_USERNAME
mysql_password = MYSQL_PASSWORD
mysql_database = MYSQL_DATABASE_NAME
db_connection = mysql.connector.connect(host=mysql_host, user=mysql_user, password=mysql_password, database=mysql_database)
db_cursor = db_connection.cursor()

# Initialize an empty string to store the conversation paragraph
conversation_paragraph = ""
conversation = []

@app.route('/chat', methods=['POST'])
def chat():
    global conversation_paragraph

    data = request.get_json()
    user_input = data.get('user_input')
    employeeId = 2000080631

    if user_input:
        print(f"User input: {user_input}")

        # Concatenate the user input to the conversation paragraph
        conversation_paragraph += "User input: " + user_input + "\n"
        print("conversation user: " + conversation_paragraph)

        # Check if user wants to exit the conversation
        if user_input.lower() == 'exit':
            print("i am in exit loop")
            # Generate response text if technical skills have been discussed
            if conversation:
                print("i am in conversation loop")
                response_text = generate_response_text(conversation_paragraph)
                print(f"AI output: {response_text}")
                # Store summary data in MySQL database
                store_summary_data(response_text, employeeId)
                return jsonify({'response_text': response_text})
            else:
                print("No technical skills were discussed, exiting...")
                return jsonify({'response_text': "Exiting the conversation. Goodbye!"})
        else:
            # Generate response text using OpenAI
            response_text = generate_response_text(user_input)
            print(f"AI output: {response_text}")
            conversation_paragraph += "AI output: " + response_text + "\n"
            print("conversation ai: " + conversation_paragraph)
            # Append user input to the conversation list
            conversation.append({"role": "user", "content": user_input})

    return jsonify({'response_text': response_text})

@app.route('/audio', methods=['POST'])
def audio():
    data = request.get_json()
    ai_input = data.get('ai_input')

    # Print the received input to the terminal
    print("Received input:", ai_input)

    if ai_input.lower() == 'exit':
        # Provide exit message
        response_text = "Exiting the conversation. Goodbye!"
        audio_base64 = ""
    else:
        audio_base64 = generate_audio(ai_input)

    return jsonify({'response_audio': audio_base64})

def generate_response_text(prompt):
    # Generate text using the assistant
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": YOUR_SYSTEM_MESSAGE},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def generate_audio(prompt):
    # Synthesize speech using Azure Speech Service
    result = speech_synthesizer.speak_text_async(prompt)
    # time.sleep(1)  # Optional delay to ensure audio is generated properly
    audio_data = result.get().audio_data

    # Encode audio data to base64
    return base64.b64encode(audio_data).decode('utf-8')

def store_summary_data(summary_text, employeeId):
    # Extract summary data
    skill_summaries = extract_summary_data(summary_text)
    
    # Create tables if not exist
    create_tables_if_not_exist()

    # Store data in MySQL database
    if skill_summaries:
        # Check if employeeId already exists
        db_cursor.execute("SELECT id FROM usersummarydataset WHERE employeeId = %s", (employeeId,))
        dataset_row = db_cursor.fetchone()
        if dataset_row:
            dataset_id = dataset_row[0]
            # Update updatedAt field
            db_cursor.execute("UPDATE usersummarydataset SET updatedAt = NOW() WHERE id = %s", (dataset_id,))
        else:
            # Insert data into usersummarydataset table if employeeId doesn't exist
            dataset_query = "INSERT INTO usersummarydataset (employeeId, createdAt, updatedAt) VALUES (%s, NOW(), NOW())"
            db_cursor.execute(dataset_query, (employeeId,))
            dataset_id = db_cursor.lastrowid
        
        # Insert data into usersummarygroup table if it doesn't exist
        db_cursor.execute("SELECT id FROM usersummarygroup WHERE skillsetGroup = 'TECHNICAL' AND usersummarydatasetId = %s", (dataset_id,))
        group_row = db_cursor.fetchone()
        if group_row:
            group_id = group_row[0]
        else:
            group_query = "INSERT INTO usersummarygroup (skillsetGroup, percentage, usersummarydatasetId) VALUES (%s, %s, %s)"
            db_cursor.execute(group_query, ('TECHNICAL', 0, dataset_id))
            group_id = db_cursor.lastrowid

        for skill_summary in skill_summaries:
            # Preprocess skillname: remove punctuation
            skill_name = skill_summary['skill'].rstrip('.,')
            print(skill_name)
            # Check if skillname already exists in usersummaryskillset table for the given group
            db_cursor.execute("SELECT id FROM usersummaryskillset WHERE skillname = %s AND usersummarygroupId = %s", (skill_name, group_id))
            skill_row = db_cursor.fetchone()
            if skill_row:
                skill_id = skill_row[0]
                # Update skillname data in usersummaryskillset table
                skillset_query = "UPDATE usersummaryskillset SET percentage = %s, scale = %s, experience = %s WHERE id = %s"
                db_cursor.execute(skillset_query, (skill_summary['percentage'], skill_summary['scale'], skill_summary['experience'], skill_id))
            else:
                # Insert new skillname data into usersummaryskillset table
                skillset_query = "INSERT INTO usersummaryskillset (skillname, percentage, scale, experience, usersummarygroupId) VALUES (%s, %s, %s, %s, %s)"
                db_cursor.execute(skillset_query, (skill_name, skill_summary['percentage'], skill_summary['scale'], skill_summary['experience'], group_id))

        # Commit the transaction
        db_connection.commit()

def extract_summary_data(summary_text):
    # Regular expressions to match skillname, experience, scale, and percentage
    skill_pattern = re.compile(r'Skill: (.+)')
    experience_pattern = re.compile(r'Experience: (\d+)')
    scale_pattern = re.compile(r'Scale: (\d+)')
    percentage_pattern = re.compile(r'Percentage: ([\d.]+)')

    # Extracting skill summaries
    skill_matches = skill_pattern.findall(summary_text)
    experience_matches = experience_pattern.findall(summary_text)
    scale_matches = scale_pattern.findall(summary_text)
    percentage_matches = percentage_pattern.findall(summary_text)

    skill_summaries = []

    for skill, experience, scale, percentage in zip(skill_matches, experience_matches, scale_matches, percentage_matches):
        skill_summary = {
            'skill': skill,
            'experience': experience,
            'scale': scale,
            'percentage': percentage
        }
        skill_summaries.append(skill_summary)

    return skill_summaries
    
def create_tables_if_not_exist():
    try:
        # Establish connection to MySQL database
        db = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USERNAME,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE_NAME,
            # port=MYSQL_PORT
        )

        # Create cursor to execute SQL queries
        cursor = db.cursor()

        # Create skilldataset table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usersummarydataset (
            id INT AUTO_INCREMENT PRIMARY KEY,
            employeeId INT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (employeeId) REFERENCES employee(id)
            )
                    """)

        # Create skilldatasetgroup table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usersummarygroup (
  id INT AUTO_INCREMENT PRIMARY KEY,
  skillsetGroup VARCHAR(255),
  percentage FLOAT,
  usersummarydatasetId INT,
  FOREIGN KEY (usersummarydatasetId) REFERENCES usersummarydataset(id)
)
        """)

        # Create skillset table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usersummaryskillset (
  id INT AUTO_INCREMENT PRIMARY KEY,
  skillname VARCHAR(255),
  percentage FLOAT,
  scale VARCHAR(255),
  experience VARCHAR(255),
  usersummarygroupId INT,
  FOREIGN KEY (usersummarygroupId) REFERENCES usersummarygroup(id)
)
        """)

        # Commit changes and close cursor and database connection
        db.commit()
        cursor.close()
        db.close()

    except Error as e:
        raise Exception(f"Error occurred while creating tables: {e}")

if __name__ == '__main__':
    app.run(debug=True)

