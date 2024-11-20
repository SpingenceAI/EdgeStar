# Services

This directory contains various microservices that can be run using Docker Compose.

## Available Services

### Ollama
- GPU-enabled LLM service using Ollama
- Exposed on port 15703 (configurable via OLLAMA_EXPOSE_PORT)
- Supports parallel inference and multiple loaded models
- Data stored in `./data/ollama_data`

### STT (Speech-to-Text)
- GPU-enabled speech recognition service
- Exposed on port 15706 (configurable via STT_EXPOSE_PORT)
- Uses FastAPI with auto-reload enabled
- Models stored in `./data/stt/models`
- Logs stored in `./data/logs/stt`


## Configuration

Environment variables can be configured in `services/envs/.env`. See `.env.example` for available options:

- SERVICES_DIR: Directory containing service files (default: ./services)
- DATA_MOUNT_POINT: Directory for persistent data storage (default: ./data)
- OLLAMA_EXPOSE_PORT: Port for Ollama service (default: 15703)
- STT_EXPOSE_PORT: Port for STT service (default: 15706)

## Usage

To start all services:
```bash
# create network if not exists
docker network create edgestar-network
# modify envs/.env
docker compose --env-file envs/.env.example up -d
```

### Check if the services are running
```bash
# ollama
curl http://localhost:15703
# stt
curl http://localhost:15706
```