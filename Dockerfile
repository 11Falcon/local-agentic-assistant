FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY core/ ./core/
COPY agents/ ./agents/
COPY assistant.py .

ENV PYTHONUNBUFFERED=1 \
    LLM_BASE_URL=http://host.docker.internal:11434/v1 \
    EMBED_BASE_URL=http://host.docker.internal:11434/v1 \
    QWEN_MODEL=qwen3:4b


CMD ["python", "assistant.py"]