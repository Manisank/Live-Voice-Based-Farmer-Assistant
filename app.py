import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, ClientSettings
import json
import requests
from google.cloud import texttospeech
import os

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
        </style>
        """,
        unsafe_allow_html=True,
    )

# Set up Google Cloud credentials
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
    with open("google_api_key.json", "w") as f:
        f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_api_key.json"
else:
    st.error("Google API credentials missing. Set them in Streamlit Secrets.")
    st.stop()

# Hugging Face settings
HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HUGGING_FACE_API_TOKEN = st.secrets.get("HUGGING_FACE_API_TOKEN")
if not HUGGING_FACE_API_TOKEN:
    st.error("Hugging Face API token is missing. Set it in Streamlit Secrets.")
    st.stop()

headers = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}

# Generate response from Hugging Face
def generate_response_falcon(query):
    payload = {"inputs": query, "parameters": {"max_new_tokens": 150}}
    response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        return f"Error: {response.status_code}"

# Google Cloud Text-to-Speech
def text_to_speech(text):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
    return "output.mp3"
from streamlit_webrtc import webrtc_streamer, RTCConfiguration

# Configure STUN Server
RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]}  # Google's free STUN server
        ]
    }
)

# Inside your main function or WebRTC section
ctx = webrtc_streamer(
    key="live-voice",
    rtc_configuration=RTC_CONFIGURATION,
    media_stream_constraints={"audio": True, "video": False},  # Only audio
    async_processing=True,
)


from streamlit_webrtc import webrtc_streamer, WebRtcMode

def main():
    st.title("🌾 Live Voice-Based Farmer Assistant 🌾")
    st.write("🎤 Speak your question about farming, agriculture, or food systems, and hear a concise response!")

    ctx = webrtc_streamer(
        key="example",
        mode=WebRtcMode.SENDRECV,  # Correct usage of WebRtcMode
        media_stream_constraints={"audio": True, "video": False},
    )

    if ctx.audio_receiver and st.button("Process Audio"):
        audio_frames = ctx.audio_receiver.get_frames()
        for frame in audio_frames:
            # Process the audio frames here
            st.write("Audio received and processed!")

if __name__ == "__main__":
    main()
