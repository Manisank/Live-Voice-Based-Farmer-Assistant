# Use the official Python 3.12 image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application files to the container
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    python3-distutils \
    python3-apt \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port Streamlit will use
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
