# Kai Voice Call Agent

A LiveKit-based voice call agent that provides AI-powered conversation capabilities with support for multiple AI services including OpenAI, Simli, and Bey.

## Features

- **LiveKit Integration**: Built on LiveKit for real-time voice communication
- **Multi-AI Support**: OpenAI GPT, Simli, and Bey AI services
- **Noise Cancellation**: Built-in noise cancellation for better audio quality
- **Language Level Support**: CEFR language proficiency levels (A1-C2)
- **Langfuse Integration**: Observability and analytics for AI conversations
- **Docker Support**: Containerized deployment for production environments

## Prerequisites

- Python 3.11.6 or higher
- Docker and Docker Compose (for production deployment)
- Required API keys and credentials (see Environment Variables section)

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Kai-Voice-Call
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the required variables (see Environment Variables section below).

5. **Download required models** (if needed)
   ```bash
   python3 agent.py download-files
   ```

### Production Deployment

1. **Build the Docker image**
   ```bash
   docker build -t kai-voice-call-agent:latest .
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# LiveKit Configuration
LIVEKIT_API_KEY=your_livekit_api_key_here
LIVEKIT_API_SECRET=your_livekit_api_secret_here
LIVEKIT_URL=your_livekit_url_here

# Langfuse Configuration (Observability)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
LANGFUSE_HOST=your_langfuse_host_here

# Kai API Configuration
KAI_API_BASE_URL=your_kai_api_base_url_here
KAI_API_SECRET_KEY=your_kai_api_secret_key_here

# Simli AI Configuration
SIMLI_API_KEY=your_simli_api_key_here
SIMLI_FACE_ID=your_simli_face_id_here

# Bey AI Configuration
BEY_API_KEY=your_bey_api_key_here

# Prompts Configuration (optional)
PROMPTS_FILE=prompts.json
```

## Usage

### Local Development

Run the agent in development mode:
```bash
python3 agent.py dev
```

### Production

The agent runs automatically when started via Docker:
```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f kai-agent

# Stop the service
docker-compose down
```

### Available Commands

- `python3 agent.py dev` - Run in development mode
- `python3 agent.py start` - Start the production agent
- `python3 agent.py download-files` - Download required model files

## Dependencies

The project uses the following key dependencies:

- **LiveKit Agents**: Core voice call functionality
- **OpenAI**: GPT integration for conversation
- **Simli**: AI voice and face processing
- **Bey**: Additional AI capabilities
- **Langfuse**: Observability and analytics
- **Pydantic**: Data validation and settings management
- **HTTPX**: HTTP client for API calls

See `requirements.txt` for the complete list of dependencies.

## Project Structure

```
Kai-Voice-Call/
├── agent.py              # Main agent application
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker build configuration
├── requirements.txt      # Python dependencies
├── prompts.json          # AI prompt configurations
├── models/               # Data models
│   ├── __init__.py
│   └── language_level.py # CEFR language levels
└── KMS/                  # Key Management System
    └── logs/             # Application logs
```

## API Endpoints

The agent exposes the following endpoints:

- **Port 8081**: Main agent service
- **Health Check**: Available at `/health` (if implemented)
- **WebSocket**: LiveKit WebSocket connections

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**: Ensure all required environment variables are set in your `.env` file
2. **API Key Errors**: Verify your API keys are correct and have sufficient permissions
3. **Port Conflicts**: Ensure port 8081 is available for the agent service
4. **Model Download Issues**: Run `python3 agent.py download-files` to ensure all required models are available

### Logs

- **Local Development**: Check console output for error messages
- **Production**: View Docker logs with `docker-compose logs -f kai-agent`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For support and questions, please [add contact information or create an issue in the repository].