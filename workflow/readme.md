# Workflow

This directory contains configurable AI agent workflows that combine multiple services for specific applications.
Agents are built upon langgraph, langchain.

## Overview

The workflow component allows you to create custom AI pipelines by combining different services like:

- chatbot : basic llm chatbot
- rag: retrieval augmented generation
- data summarizer: summarize data, data source can be files(pdf, docx, etc.) or urls or youtube videos
- meeting recap: summarize meeting content

## Interfaces

- Web UI (ui_st[streamlit])
  - chatbot
  - rag
  - data summarizer
  - web search
- CLI (playground_cli.py)
  - chatbot
  - rag
  - data summarizer
  - meeting recap
  - web search
- Mail service
  - Microsoft Graph API
  - Gmail API
- API (working in progress)

## Environment Setup

1. run services (ollama, stt, SearxNG), follow instructions in [service readme](../services/readme.md)
2. create network (if not already created)

```bash
docker network create edgestar-network
```

3. configure envs/.env.example
   - OLLAMA_MODEL: the model name to use for ollama (ex: llama3.2:latest)
   - TAVILY_API_KEY: the api key for tavily (ex: tvly-xxxxxxxxxxxxxxxxxxxxxxxx) (optional)
4. pull ollama model [refernece](https://github.com/ollama/ollama/blob/main/docs/api.md#pull-a-model)

```bash
curl http://localhost:15703/api/pull -d '{"model": "llama3.2:latest"}'
```

5. check if ollama model is pulled

```bash
curl http://localhost:15703/api/tags
```

6. build docker image for workflow

```bash
docker build -t edgestar/workflow .
```

7. Configure configs/agents.yml output translation language
   some agents have output translation, you can configure the language here

```yaml
data_summarizer:
  output_translation:
    language: zh-tw
rag:
  output_translation:
    language: zh-tw
rag_memory:
  output_translation:
    language: zh-tw
```

## RUN Workflow

### Playground CLI

run playground cli, mode: example, will mount current directory to /workspace and use envs/.env.example

```bash
docker run --rm -it -v ${PWD}:/workspace --network edgestar-network --name workflow-playground edgestar/workflow python playground_cli.py --env envs/.env.example
```

### WEB UI

- CHATBOT: http://localhost:15401
- RAG: http://localhost:15402
- DATA SUMMARIZER: http://localhost:15403
- WEB SEARCH: http://localhost:15404

```bash
docker compose -f UI-docker-compose.yml --env-file envs/.env.example up
```

### Mail Service

Follow instructions in [mail readme](./mail/readme.md)

```bash
docker compose -f mail-docker-compose.yml --env-file envs/.env.example up
```
