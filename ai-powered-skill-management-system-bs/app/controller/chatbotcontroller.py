from flask import Blueprint, request, jsonify
from app.service.chatbotservice import generate_response_text, store_summary_data, generate_audio
# import io
# import time
# import re
# import base64
# import mysql.connector 
from mysql.connector import Error
from flask import Flask, jsonify, request
from flask_cors import CORS
# from azure.cognitiveservices.speech import SpeechConfig, AudioConfig, SpeechSynthesizer
# from openai import AzureOpenAI
# from config import YOUR_SPEECH_KEY, YOUR_SPEECH_REGION, YOUR_OPENAI_API_KEY, YOUR_OPENAI_ENDPOINT, YOUR_SYSTEM_MESSAGE, MYSQL_HOST, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE_NAME


# Create a Blueprint for the skill dataset controller
chatbot_bp = Blueprint('chatbot_bp', __name__)
CORS(chatbot_bp)  # This will enable CORS for all routes of your Flask app



# Initialize an empty string to store the conversation paragraph
conversation_paragraph = ""
conversation = []

@chatbot_bp.route('/chat', methods=['POST'])
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

@chatbot_bp.route('/audio', methods=['POST'])
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