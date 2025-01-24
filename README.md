# Live Voice-Based Farmer Assistant

## Overview
The **Live Voice-Based Farmer Assistant** is a Streamlit application that enables farmers to ask voice-based queries related to farming, agriculture, and food systems. This application uses **Google Speech-to-Text API**, **Google Text-to-Speech API**, and **Hugging Face Falcon-7B LLM** to provide concise, relevant responses. Initially, the application leveraged an encyclopedia PDF for knowledge extraction but later integrated **LLM** for improved accuracy.

---

## Workflow Overview

### Initial Approach: PDF-Based Knowledge Extraction
1. Preprocessed the **Encyclopedia of Agriculture and Food Systems** PDF using `pdfplumber`, `nltk`, and **SentenceTransformers**.
2. Extracted sentences and stored embeddings in an SQLite database.
3. Queried the database for responses.
4. **Challenges Faced**:
   - Responses from the PDF were not always relevant or accurate.
   - PDF preprocessing took significant time and often crashed due to memory issues.

### Enhanced Approach: Predefined Responses and LLM
1. Integrated **predefined responses** in JSON format for common queries.
2. Used **Hugging Face Falcon-7B LLM** as a fallback to generate accurate, context-aware responses when no predefined response was available.
3. Converted text responses into audio using the **Google Text-to-Speech API**.
4. Created a **Streamlit interface** for live interaction.

---

## Key Features

### Final Application Features
1. **Speech-to-Text**:
   - Converts live voice queries into text using the **Google Speech-to-Text API**.
2. **Predefined Responses**:
   - Answers frequently asked questions from a predefined JSON file.
3. **LLM Integration**:
   - Uses **Hugging Face Falcon-7B LLM** for generating context-aware responses when predefined responses are unavailable.
4. **Text-to-Speech**:
   - Converts responses into audio using the **Google Text-to-Speech API**.
5. **User-Friendly Interface**:
   - Designed with a visually appealing **Streamlit** interface for interaction.

---

## Installation Guide

### Prerequisites
1. Python 3.8 or above.
2. A Google Cloud account with the **Speech-to-Text** and **Text-to-Speech** APIs enabled.
3. A Hugging Face account with an API token.
4. Predefined responses stored in a JSON file (`predefined_responses.json`).

---

### Steps to Set Up Google Cloud APIs
1. **Create a Google Cloud Account**:
   - Visit [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. **Enable APIs**:
   - Enable **Speech-to-Text** and **Text-to-Speech APIs** from the **API & Services** section.
3. **Create a Service Account**:
   - Navigate to **IAM & Admin > Service Accounts**.
   - Create a service account and assign the necessary permissions.
   - Generate and download a JSON key file for the service account.
4. **Save the JSON Key**:
   - Save the JSON file as `google_api_key.json` in the root directory of the project.

---

### Steps to Install the Application
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Live-Voice-Based-Farmer-Assistant
