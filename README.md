
![image](./images/EdgeStar_logo.png)

# EdgeStar


EdgeStar is a modular AI platform consisting of two main components:

1. **Services** - A collection of microservices for hosting AI models and capabilities
2. **Workflow** - Configurable AI agent workflows for specific applications

## Services

The services component provides containerized microservices for various AI capabilities:

- **Ollama** - GPU-enabled LLM service for running open source language models
  - Exposed on port 15703 (configurable)
  - Supports parallel inference and multiple loaded models
  - Data stored in `./data/ollama_data`

- **STT (Speech-to-Text)** - GPU-enabled speech recognition service
  - Exposed on port 15706 (configurable) 
  - FastAPI backend with auto-reload
  - Models stored in `./data/stt/models`

See the [Services README](services/readme.md) for detailed configuration and usage instructions.

## Workflow

The workflow component allows you to create custom AI pipelines by combining different services like chatbots, RAG systems, data summarizers, and meeting recap tools. It is built upon langgraph and langchain.

### Interfaces

- **Web UI (ui_st)**
  - Chatbot interface
  - RAG (Retrieval Augmented Generation) 
  - Data summarizer
- **CLI** via playground_cli.py
- **Mail Service**
  - Microsoft Graph API integration
  - Gmail integration (in progress)
- **API** (in development)

See the [Workflow README](workflow/readme.md) for detailed configuration and usage instructions.


## ROADMAPS

- [ ] HTTP API
- [ ] Mail Service
- [ ] Translation Agent
- [ ] Agent Refactoring