import streamlit as st
import os
import io
import requests
import queue
import numpy as np
import wave
from google.cloud import texttospeech
import json
import speech_recognition as sr

# Apply Custom CSS
def apply_custom_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #121212;
            color: #FFFFFF;
        }
        .main-content {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #FFFFFF;
        }
        .stButton > button {
            background-color: #FFFFFF;
            color: #000000;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            padding: 8px 16px;
        }
        .stTextArea textarea {
            background-color: #1E1E1E;
            color: #FFFFFF;
            border: 1px solid #FFFFFF;
            border-radius: 8px;
            padding: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Set up Google Cloud credentials
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
    from google.oauth2.service_account import Credentials
    credentials = Credentials.from_service_account_info(json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"]))
    st.write("Google API credentials loaded.")
else:
    st.error("Google API credentials not found! Please set GOOGLE_APPLICATION_CREDENTIALS_JSON in your environment variables.")

# Hugging Face Configuration
HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN")
if not HUGGING_FACE_API_TOKEN:
    st.error("Hugging Face API token is missing!")
HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HEADERS = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}

# Speech-to-Text Function
def live_speech_to_text():
    recognizer = sr.Recognizer()
    st.info("Please upload a .wav file for speech recognition.")
    uploaded_file = st.file_uploader("Upload .wav file", type=["wav"])
    if uploaded_file:
        with wave.open(uploaded_file, "rb") as wf:
            audio_data = wf.readframes(wf.getnframes())
            audio = sr.AudioFile(io.BytesIO(audio_data))
            with audio as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    return text
                except sr.UnknownValueError:
                    st.error("Google Speech Recognition could not understand the audio.")
                except sr.RequestError as e:
                    st.error(f"Error with Google Speech Recognition service: {e}")

# Text-to-Speech Function
def text_to_speech(text):
    client = texttospeech.TextToSpeechClient(credentials=credentials)
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    st.audio(response.audio_content, format="audio/mp3")

# Generate Response using Hugging Face
def generate_response_falcon(query):
    payload = {"inputs": query, "parameters": {"max_new_tokens": 150}}
    response = requests.post(HUGGING_FACE_API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        st.error(f"Hugging Face API error: {response.status_code}")
        return "Could not generate a response."

# Streamlit App
def main():
    apply_custom_styles()
    st.title("🌾 Voice-Based Farmer Assistant 🌾")
    st.write("🎤 Upload your voice query and get a response!")
    query = live_speech_to_text()
    if query:
        st.success(f"Recognized Query: {query}")
        response = generate_response_falcon(query)
        st.text_area("Generated Response", response, height=150)
        if response:
            text_to_speech(response)

if __name__ == "__main__":
    import os
    # Get the port from the environment (for platforms like Render or Heroku)
    port = os.environ.get("PORT", 8501)  # Default to 8501 if PORT is not set
    # Start the Streamlit app on the specified port
    os.system(f"streamlit run app.py --server.port {port} --server.address 0.0.0.0")
    main()


