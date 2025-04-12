# AI Assistant

This project is an AI assistant, powered by selected Ollama model, that can take commands from text or through voice recognition. The assistant can provide weather updates for any city, read and manage Gmail messages, and more.

## Features

- **Voice Recognition**: Convert voice commands into text.
- **Text Commands**: Accept commands directly through text input.
- **Weather Updates**: Get weather information for any city.
- **Gmail Integration**: Read and manage Gmail messages.

## Installation

1.  You need to have Ollama CLI on your computer to run the assistant or run the ollama/ollama container. \
    1.1 You can download Ollama CLI [here](https://ollama.com/download/) \
    1.2 You can check out how to run ollama/ollama container [here](https://hub.docker.com/r/ollama/ollama)

2.  Clone the repository:

    ```bash
    git clone https://github.com/JakubTuta/AI-assistant.git
    ```

3.  Navigate to the project directory:

    ```bash
    cd ai-assistant
    ```

4.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Before starting application

You need to create Voice Recognition credentials

1. Create new project on Google Cloud Platform
2. Enable [Cloud Text-to-Speech API](https://console.cloud.google.com/marketplace/product/google/texttospeech.googleapis.com)
3. Get project credentials json file, rename it to gcp_credentials.json and place in credentials directory in the main directory

## Usage

### First run of the program

You are gonna need to log into your Gmail account through the console to enable the Gmail API

## Running the program

1. Open a console and type:

   ```bash
   ollama serve
   ```

   1.1 (optionally) run a ollama/ollama container

2. Now you can run the AI assistant program:
   ```bash
   python assistant.py
   ```
