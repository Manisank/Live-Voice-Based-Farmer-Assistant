import streamlit as st
import os
import requests
import speech_recognition as sr
from google.cloud import texttospeech
import json
import os

import os
import streamlit as st

# Check if running locally or in Streamlit Cloud
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
elif "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
    # Write the Google API key JSON to a temporary file for use on Streamlit Cloud
    with open("google_api_key.json", "w") as f:
        f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_api_key.json"
else:
    raise ValueError("Google API credentials are missing. Set 'GOOGLE_APPLICATION_CREDENTIALS' or use Streamlit Secrets.")

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the Hugging Face token
HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN")
HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"

headers = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}

# Load predefined responses from JSON file
def load_predefined_responses(json_file="predefined_responses.json"):
    try:
        with open(json_file, "r") as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Failed to load predefined responses: {e}")
        return {}

# Speech-to-Text Function
def live_speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Speak now!")
        try:
            audio = recognizer.listen(source, timeout=5)
            st.success("Voice captured. Processing...")
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            st.error("Sorry, I couldn't understand what you said. Please try again.")
            return None
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Speech Recognition service; {e}")
            return None

# Text-to-Speech Function
def text_to_speech(text, output_file="output.mp3"):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    with open(output_file, "wb") as out:
        out.write(response.audio_content)
    return output_file

# Generate Response using Hugging Face API
def generate_response_falcon(query):
    prompt = f"Answer concisely about farming, agriculture, or food systems:\n\n{query}\n\nAnswer:"
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 150}}
    response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        raw_response = response.json()[0]["generated_text"]
        answer = raw_response.split("Answer:")[-1].strip()
        return answer
    else:
        st.error(f"Error with Hugging Face API: {response.status_code}")
        return "I'm sorry, I couldn't generate a response. Please try again."

# Check for predefined responses
def get_predefined_response(query, predefined_responses):
    query_lower = query.lower()
    return predefined_responses.get(query_lower, None)

# Apply custom styles and dark theme
def apply_custom_styles():
    st.markdown(
        """
        <style>
        /* Dark theme background and text */
        .stApp {
            background-color: #121212;
            color: #FFFFFF;
        }
        .main-content {
            background: rgba(255, 255, 255, 0.1); /* Semi-transparent white */
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #FFFFFF;
        }
        .stButton>button {
            background-color: #FFFFFF; /* White button */
            color: #000000; /* Black text */
            font-size: 18px;
            font-weight: bold;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
        }
        .stButton>button:hover {
            background-color: #EEEEEE; /* Lighter white */
        }
        h1, h2, h3 {
            color: #FFFFFF !important;
            text-shadow: 1px 1px 2px #000000;
        }
        .stTextArea textarea {
            background-color: #1E1E1E; /* Dark gray */
            color: #FFFFFF; /* White text */
            border: 1px solid #FFFFFF;
            border-radius: 8px;
            padding: 5px;
            font-size: 16px;
        }
        .stInfo {
            background-color: rgba(255, 255, 255, 0.1);
            color: #FFFFFF;
            border: 1px solid #FFFFFF;
            padding: 10px;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Streamlit App
def main():
    apply_custom_styles()
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.title("🌾 Live Voice-Based Farmer Assistant 🌾")
    st.write("🎤 Speak your question about farming, agriculture, or food systems, and hear a concise response!")

    # Load predefined responses from JSON
    predefined_responses = load_predefined_responses()

    if st.button("Speak Now"):
        query = live_speech_to_text()
        if query:
            st.success(f"Recognized Query: {query}")
            # Check predefined responses first
            response = get_predefined_response(query, predefined_responses)
            if response:
                st.info("Using predefined response.")
            else:
                st.info("No predefined response found. Using LLM.")
                response = generate_response_falcon(query)

            st.write("### Response:")
            st.text_area("", response, height=150)

            # Convert the response to speech
            try:
                response_audio = text_to_speech(response)
                st.audio(response_audio, format="audio/mp3")
            except Exception as e:
                st.error(f"Text-to-Speech failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
