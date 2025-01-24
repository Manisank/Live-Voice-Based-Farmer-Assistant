import streamlit as st
import os
import requests
import tempfile
import sounddevice as sd
import wave
import queue
import time
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

# Google Cloud Credentials
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
elif "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
    with open("google_api_key.json", "w") as f:
        f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_api_key.json"
else:
    raise ValueError("Google API credentials are missing. Set 'GOOGLE_APPLICATION_CREDENTIALS' or use Streamlit Secrets.")

# Hugging Face Token and Endpoint
HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN") or st.secrets.get("HUGGING_FACE_API_TOKEN")
if not HUGGING_FACE_API_TOKEN:
    st.error("Hugging Face API token is missing. Please set it in .env or Streamlit Secrets.")
    raise ValueError("Hugging Face API token is required.")
headers = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}

# Load predefined responses
def load_predefined_responses(json_file="predefined_responses.json"):
    try:
        with open(json_file, "r") as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Failed to load predefined responses: {e}")
        return {}

# Speech-to-Text Function
def live_speech_to_text():
    st.info("Listening... Speak now!")
    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time, status):
        if status:
            st.error(f"SoundDevice error: {status}")
        audio_queue.put(indata.copy())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav_file:
        try:
            with sd.InputStream(callback=audio_callback, channels=1, samplerate=16000, dtype="int16"):
                st.info("Recording for 5 seconds...")
                sd.sleep(5000)

            with wave.open(tmp_wav_file.name, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                while not audio_queue.empty():
                    wf.writeframes(audio_queue.get())

            recognizer = sr.Recognizer()
            with sr.AudioFile(tmp_wav_file.name) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                return text
        except sr.UnknownValueError:
            st.error("Sorry, I couldn't understand what you said.")
            return None
        except sr.RequestError as e:
            st.error(f"Error with Google Speech Recognition service: {e}")
            return None
        except Exception as e:
            st.error(f"Error during speech recognition: {e}")
            return None
        finally:
            try:
                tmp_wav_file.close()
                os.remove(tmp_wav_file.name)
            except Exception as delete_error:
                st.warning(f"Error deleting temporary file: {delete_error}")

# Text-to-Speech Function
# Text-to-Speech Function
def text_to_speech(text, output_file="output.mp3"):
    try:
        client = texttospeech.TextToSpeechClient()

        # Split long text into manageable chunks for TTS
        max_chunk_size = 500  # Google TTS character limit per request
        chunks = [text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]
        audio_content = b""

        for chunk in chunks:
            synthesis_input = texttospeech.SynthesisInput(text=chunk)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            audio_content += response.audio_content

        # Write the combined audio content to the output file
        with open(output_file, "wb") as out:
            out.write(audio_content)
        return output_file
    except Exception as e:
        st.error(f"Text-to-Speech failed: {e}")
        return None

# Generate Response using Hugging Face
# Generate Response using Hugging Face
# Generate Response using Hugging Face
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
    return predefined_responses.get(query.lower(), None)

# Streamlit App
def main():
    apply_custom_styles()
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.title("🌾 Live Voice-Based Farmer Assistant 🌾")
    st.write("🎤 Speak your question about farming, agriculture, or food systems, and hear a concise response!")

    predefined_responses = load_predefined_responses()

    if st.button("Speak Now"):
        query = live_speech_to_text()
        if query:
            st.success(f"Recognized Query: {query}")
            response = get_predefined_response(query, predefined_responses)
            if response:
                st.info("Using predefined response.")
            else:
                st.info("No predefined response found. Using LLM.")
                response = generate_response_falcon(query)

            st.write("### Response:")
            st.text_area("", response, height=150)
            tts_output = text_to_speech(response)
            if tts_output:
                st.audio(tts_output, format="audio/mp3")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
