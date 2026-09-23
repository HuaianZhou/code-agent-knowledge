# Base runtime only. Derive an image that installs your chosen coding-agent CLI.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "PyYAML>=6,<7" "sqlite-vec>=0.1.6,<0.2"
ARG EMBEDDING_MODEL
ARG EMBEDDING_REVISION
ENV HF_HOME=/opt/embedding-cache
# Bake a pinned model into the image so sandboxed capture never needs model downloads.
RUN test -n "$EMBEDDING_MODEL" && test -n "$EMBEDDING_REVISION" \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir "sentence-transformers>=3,<6" \
    && python -c 'import os; from sentence_transformers import SentenceTransformer; SentenceTransformer(os.environ["EMBEDDING_MODEL"], revision=os.environ["EMBEDDING_REVISION"], trust_remote_code=False)'
ENV HF_HUB_OFFLINE=1
COPY adapter.py /opt/evaluation-adapter.py
ENTRYPOINT ["python", "/opt/evaluation-adapter.py"]
