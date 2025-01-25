import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, ClientSettings
import requests
import os
from google.cloud import texttospeech
import json
import queue

# Apply Custom Styles
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

# Google Cloud Credentials
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
    with open("google_api_key.json", "w") as f:
        f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_api_key.json"

# Hugging Face API
HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN") or st.secrets.get("HUGGING_FACE_API_TOKEN")
headers = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}

# Text-to-Speech
def text_to_speech(text, output_file="output.mp3"):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
    return output_file

# Hugging Face Response Generator
def generate_response_falcon(query):
    payload = {"inputs": query, "parameters": {"max_new_tokens": 150}}
    response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        return "Sorry, I couldn't generate a response. Please try again."

# WebRTC Audio Processor
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = queue.Queue()

    def recv(self, frame):
        self.frames.put(frame.to_ndarray())
        return frame

def main():
    apply_custom_styles()
    st.title("🌾 Live Voice-Based Farmer Assistant 🌾")
    st.write("🎤 Speak your question about farming, and get a response!")

    # WebRTC Config
    ctx = webrtc_streamer(
        key="speech-to-text",
        mode=ClientSettings.Mode.SENDRECV,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        audio_processor_factory=AudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
    )

    if ctx.audio_processor:
        st.info("Listening... Speak now!")
        if st.button("Process Query"):
            if not ctx.audio_processor.frames.empty():
                st.success("Processing...")
                # Generate response using Hugging Face
                query = "Your question here"  # Placeholder
                response = generate_response_falcon(query)
                st.write("### Response:")
                st.write(response)
                tts_output = text_to_speech(response)
                st.audio(tts_output, format="audio/mp3")
            else:
                st.warning("No audio input received.")

if __name__ == "__main__":
    main()
