# AI Assistant

A versatile personal assistant powered by AI that accepts both text and voice commands. Use it to check weather, manage Gmail, control Spotify, and more - all through natural language.

## Features

- **Multiple Input Methods**
  - Voice commands (with speech recognition)
  - Text commands
  
- **Integrations**
  - Weather information for any location
  - Gmail account management
  - Spotify music control (play songs, albums, artists)

- **AI Model Options**
  - Anthropic Claude Sonnet (via API key)
  - Ollama models (locally installed)

### To see all commands, see commands.json file

## Quick Start Guide

### 1. Set Up Environment

```bash
# Clone the repository
git clone https://github.com/JakubTuta/AI-assistant.git
cd ai-assistant

# Create and activate virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure AI Model

Choose ONE of the following options:

#### Option A: Use Anthropic Claude Sonnet
1. Obtain an API key from Anthropic
2. Add to your `.env` file:
   ```
   ANTHROPIC_API_KEY="your_api_key"
   ```

#### Option B: Use Ollama locally
1. Install Ollama:
   - Download from [ollama.com/download](https://ollama.com/download/)
   - OR use Docker: [Docker Hub - ollama/ollama](https://hub.docker.com/r/ollama/ollama)
2. Add to your `.env` file:
   ```
   AI_MODEL="your_ollama_model_name"
   ```

### 3. Set Up Spotify Integration

1. Create a Spotify Developer account at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Register a new application
3. Set the Redirect URI to `http://127.0.0.1:8888/callback`
4. Add Spotify credentials to your `.env` file:
   ```
   SPOTIFY_CLIENT_ID="your_spotify_client_id"
   SPOTIFY_CLIENT_SECRET="your_spotify_client_secret"
   ```

### 4. For Voice Commands (Optional)

If you want to use voice input:

1. Create a Google Cloud Platform project
2. Enable the [Cloud Text-to-Speech API](https://console.cloud.google.com/marketplace/product/google/texttospeech.googleapis.com)
3. Download credentials as JSON
4. Rename to `gcp_credentials.json` and place in the `credentials` directory

## Running the Assistant

### Start Ollama (if using locally)

```bash
# If installed directly
ollama serve

# If using Docker
docker run -d -p 11434:11434 ollama/ollama
```

### Launch the Assistant

```bash
# Basic text-only mode with cloud AI
python assistant.py

# With voice recognition
python assistant.py --audio  # or -a

# Using local Ollama model
python assistant.py --local  # or -l

# Both voice and local model
python assistant.py --audio --local
```

## First Run

On first execution, you'll need to authorize Gmail access:
1. The program will open a browser authentication page
2. Log in to your Gmail account
3. Grant the requested permissions
4. The token will be saved for future use

## Example Commands

- "What's the weather in London?"
- "Check my unread emails"
- "Play Bohemian Rhapsody on Spotify"

## Troubleshooting

- **Voice Recognition Issues**: Ensure your microphone is set as the default input device
- **Ollama Connection Errors**: Verify Ollama is running on the expected port (11434)
- **Spotify Authentication Failures**: Double-check that your redirect URI matches exactly