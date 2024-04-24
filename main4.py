import os
import time
import json
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI


api_key = "e8bf9ff9c9cc4fd9b1da9bf7bf779ea5"
endpoint = "https://textassistance.openai.azure.com/"


speech_key = "e67ce8edd8174a89b84466bde5f92ea4"
speech_region = "northcentralus"

# Initialize Azure Speech Service client
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

client = AzureOpenAI(
    api_key=api_key,
    api_version="2024-02-15-preview",
    azure_endpoint=endpoint
)


def generate_text(prompt):
    # Generate text using the assistant
    response = client.chat.completions.create(
        model="gpt-35-turbo",
        messages=[
            {"role": "system", "content": """
    If a user interacts with you, the first thing you need to ask is a question regarding their skills, not how can I assist you today.
    You are a data collector that asks for information about user skills, experience, project experience, and domain knowledge. 
    At last, you will give a final output that includes the data you have collected and verify it with the user. and print the collected data as table

    Ask question one by one. If the user mentions skills, ask for each skill information. 
    Make it short and sweet, and ask the user if they want to exit the chat every time. 
    If yes, ask them to enter 'exit'.
    """},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def synthesize_speech(text):
    # Synthesize speech using Azure Speech Service
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = speech_synthesizer.speak_text_async(text)
    result.get()


def recognize_speech():
    # Recognize speech using Azure Speech Service
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("Listening for speech...")
    result = speech_recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized")
        return None
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
        return None
# Loop for interaction
conversation = []

while True:
    # Get user input (speech) using Azure Speech Service
    user_input = recognize_speech()
    if user_input:
        print(f"User input: {user_input}")  

        # Check if user wants to exit the conversation
        if user_input.lower() == 'exit':
            print("Exiting the conversation.")
            break

        # Generate response text using OpenAI
        response_text = generate_text(user_input)
        print(f"AI output: {response_text}")  

        # Convert response text to speech using Azure Speech Service
        synthesize_speech(response_text)

        # Append user input and AI output to the conversation list
        conversation.append({"role": "user", "content": user_input})
        conversation.append({"role": "assistant", "content": response_text})

# Print the conversation
for message in conversation:
    print(f"{message['role'].capitalize()}: {message['content']}")
