FROM python:3.12-slim as base

FROM base as builder

COPY requirements.txt .
RUN pip install -r requirements.txt
WORKDIR /workspace
