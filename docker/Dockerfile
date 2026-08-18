# The assistant only. Ollama stays on the host - it already has the models and
# the GPU, and this container reaches it over HTTP via host.docker.internal.
FROM python:3.11-slim

# Your network intercepts TLS, so pip needs these hosts trusted (same reason you
# needed --trusted-host locally). Harmless on a normal network.
ARG PIP_TRUSTED="--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org"

WORKDIR /app

# Dependencies first: this layer is cached and only rebuilds when requirements
# change, so editing your code gives you a ~2 second rebuild instead of 2 minutes.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip $PIP_TRUSTED \
 && pip install --no-cache-dir $PIP_TRUSTED -r requirements.txt

COPY core/ ./core/
COPY agents/ ./agents/
COPY assistant.py .

# Don't run as root. Secrets arrive as bind mounts owned by the host, and a
# container that never needs root shouldn't have it.
RUN useradd --create-home --uid 1000 assistant \
 && mkdir -p /app/session /app/notes \
 && chown -R assistant:assistant /app
USER assistant

# Defaults; docker-compose overrides them.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LLM_BASE_URL=http://host.docker.internal:11434/v1 \
    EMBED_BASE_URL=http://host.docker.internal:11434/v1 \
    QWEN_MODEL=qwen3:4b \
    EMBED_MODEL=nomic-embed-text \
    NO_INTERACTIVE_AUTH=1

CMD ["python", "assistant.py"]
