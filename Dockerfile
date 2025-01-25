# Use a lightweight Python 3.12 image
FROM python:3.12-slim

# Install system dependencies for sounddevice and others
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy all project files to the container
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port Streamlit will use
EXPOSE 8501

# Command to run your Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
