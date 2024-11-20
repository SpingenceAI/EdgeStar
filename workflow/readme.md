# Workflow

This directory contains configurable AI agent workflows that combine multiple services for specific applications.
Agents are built upon langgraph, langchain.

## Overview

The workflow component allows you to create custom AI pipelines by combining different services like:
- chatbot
- rag
- data summarizer
- meeting recap

## Interfaces
- Web UI (ui_st)
    - chatbot
    - rag
    - data summarizer
- CLI (playground_cli.py)
    - chatbot
    - rag
    - data summarizer
    - meeting recap
- Mail service (working in progress)
    - microsoft graph api
    - gmail
- API (working in progress)


## Getting Started (ENV SETUP)

1. run services (ollama, stt), follow instructions in [service readme](../services/readme.md)
2. configure envs/.env.example
    - OLLAMA_MODEL: the model name to use for ollama (ex: llama3.2:latest)
    - TAVILY_API_KEY: the api key for tavily (ex: tvly-xxxxxxxxxxxxxxxxxxxxxxxx) (optional)
3. pull ollama model [refernece](https://github.com/ollama/ollama/blob/main/docs/api.md#pull-a-model)
```bash
curl http://localhost:15703/api/pull -d '{"model": "llama3.2:latest"}'
```
4. check if ollama model is pulled
```bash
curl http://localhost:15703/api/tags
```
5. build docker image for workflow
```bash
docker build -t edgestar/workflow .
```
6. Configure configs/agents.yml output translation language
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
#### Playground CLI
run playground cli, mode: example, will mount current directory to /workspace and use envs/.env.example
```bash
docker run --rm -it -v ${PWD}:/workspace --network edgestar-network --name workflow-playground edgestar/workflow python playground_cli.py --env envs/.env.example
```

### WEB UI
```bash
docker compose -f UI-docker-compose.yml --env-file envs/.env.example up
```
