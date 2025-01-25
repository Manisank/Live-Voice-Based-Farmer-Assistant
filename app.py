import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import numpy as np
import wave
import tempfile
import requests
from google.cloud import texttospeech
import json

# Google Cloud and Hugging Face Configurations
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
    with open("google_api_key.json", "w") as f:
        f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    st.write("Google API credentials loaded.")
else:
    st.error("Google API credentials not found! Please add them to Streamlit Secrets.")

HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HUGGING_FACE_API_TOKEN = st.secrets.get("HUGGING_FACE_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}

if not HUGGING_FACE_API_TOKEN:
    st.error("Hugging Face API token not found! Please add it to Streamlit Secrets.")

# Audio Processor for Streamlit WebRTC
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_data = np.zeros((0,), dtype=np.float32)

    def recv_audio(self, frames: np.ndarray):
        self.audio_data = np.append(self.audio_data, frames)
        return frames

    def get_audio_data(self):
        return self.audio_data

# Helper Functions
def process_audio_to_text(audio_data, sample_rate):
    """Convert recorded audio to text using Google Speech API."""
    st.info("Processing audio into text...")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        with wave.open(temp_audio.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        temp_audio.seek(0)

        # Use Google Cloud Speech-to-Text
        from google.cloud import speech_v1p1beta1 as speech

        client = speech.SpeechClient()
        with open(temp_audio.name, "rb") as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code="en-US",
        )
        response = client.recognize(config=config, audio=audio)
        for result in response.results:
            return result.alternatives[0].transcript
    return None

def generate_response_from_huggingface(query):
    """Generate a response using Hugging Face LLM."""
    st.info("Generating response...")
    payload = {"inputs": query, "parameters": {"max_new_tokens": 150}}
    response = requests.post(HUGGING_FACE_API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()[0]["generated_text"].strip()
    else:
        st.error(f"Hugging Face API error: {response.status_code}")
        return "I'm sorry, I couldn't generate a response."

def text_to_speech(text):
    """Convert text to speech using Google Text-to-Speech."""
    st.info("Converting text to speech...")
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
        audio_file.write(response.audio_content)
        return audio_file.name

# Main Streamlit App
def main():
    st.title("🌾 Live Voice-Based Farmer Assistant 🌾")
    st.write("🎤 Speak your question about farming, agriculture, or food systems, and get a concise response!")

    # WebRTC Audio Streaming
    ctx = webrtc_streamer(
        key="speech-to-text",
        mode="sendrecv",
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        audio_processor_factory=AudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
    )

    if ctx and ctx.audio_processor:
        audio_data = ctx.audio_processor.get_audio_data()
        if len(audio_data) > 0:
            # Convert audio to text
            transcript = process_audio_to_text(audio_data, sample_rate=16000)
            if transcript:
                st.success(f"Recognized Query: {transcript}")
                # Generate response
                response = generate_response_from_huggingface(transcript)
                st.text_area("Response:", response, height=150)
                # Convert response to speech
                audio_file = text_to_speech(response)
                st.audio(audio_file, format="audio/mp3")


if __name__ == "__main__":
    main()
