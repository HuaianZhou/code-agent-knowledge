# Base runtime only. Derive an image that installs your chosen coding-agent CLI.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "PyYAML>=6,<7" "sqlite-vec>=0.1.6,<0.2"
COPY adapter.py /opt/evaluation-adapter.py
ENTRYPOINT ["python", "/opt/evaluation-adapter.py"]
