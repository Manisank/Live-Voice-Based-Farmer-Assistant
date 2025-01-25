import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, ClientSettings
import os
from google.cloud import texttospeech, speech
import json
import tempfile

# Apply custom styles
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


# Google Cloud Credentials setup
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
elif "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
    with open("google_api_key.json", "w") as f:
        f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_api_key.json"
else:
    raise ValueError("Google API credentials are missing. Set 'GOOGLE_APPLICATION_CREDENTIALS' or use Streamlit Secrets.")

# Hugging Face Token setup
HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN") or st.secrets.get("HUGGING_FACE_API_TOKEN")
if not HUGGING_FACE_API_TOKEN:
    st.error("Hugging Face API token is missing. Please set it in .env or Streamlit Secrets.")
    raise ValueError("Hugging Face API token is required.")
headers = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}

# Audio Processor for WebRTC
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []
        self.sample_rate = None

    def recv(self, frame):
        self.frames.append(frame)
        self.sample_rate = frame.sample_rate
        return frame

    def get_audio_data(self):
        if self.frames and self.sample_rate:
            audio_data = b"".join([frame.to_ndarray().tobytes() for frame in self.frames])
            return audio_data, self.sample_rate
        return None, None

# Text-to-Speech
def text_to_speech(text, output_file="output.mp3"):
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        return output_file
    except Exception as e:
        st.error(f"Text-to-Speech failed: {e}")
        return None

# Speech-to-Text
def speech_to_text(audio_data, sample_rate):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        sample_rate_hertz=sample_rate,
        language_code="en-US",
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    )
    response = client.recognize(config=config, audio=audio)
    return response.results[0].alternatives[0].transcript if response.results else None

# Generate Response using Hugging Face API
def generate_response_falcon(query):
    prompt = f"Answer concisely about farming, agriculture, or food systems:\n\n{query}\n\nAnswer:"
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 150}}
    response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        raw_response = response.json()[0]["generated_text"]
        return raw_response.split("Answer:")[-1].strip()
    else:
        st.error(f"Error with Hugging Face API: {response.status_code}")
        return "I'm sorry, I couldn't generate a response. Please try again."

# Streamlit App
def main():
    apply_custom_styles()
    st.title("🌾 Live Voice-Based Farmer Assistant 🌾")
    st.write("🎤 Speak your question about farming, agriculture, or food systems, and hear a concise response!")

    ctx = webrtc_streamer(
        key="speech-to-text",
        mode="SENDRECV",
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        audio_processor_factory=AudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
    )

    if ctx.audio_processor:
        audio_data, sample_rate = ctx.audio_processor.get_audio_data()
        if audio_data:
            st.info("Processing audio...")
            query = speech_to_text(audio_data, sample_rate)
            if query:
                st.success(f"Recognized Query: {query}")
                response = generate_response_falcon(query)
                st.write("### Response:")
                st.text_area("", response, height=150)
                tts_output = text_to_speech(response)
                if tts_output:
                    st.audio(tts_output, format="audio/mp3")

if __name__ == "__main__":
    main()
