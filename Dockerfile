# Procurement Audit Planner harness: one container serves the web UI and the API,
# and runs the agents' tools (Python, pdftotext) inside per-run workspaces.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends poppler-utils \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 10001 sandbox

WORKDIR /app
COPY requirements-harness.txt .
RUN pip install --no-cache-dir -r requirements-harness.txt

COPY CLAUDE.md requirements.txt ./
COPY data ./data
COPY scripts ./scripts
COPY .claude ./.claude
COPY harness ./harness
RUN mkdir -p /app/harness/runs && find /app -name "__pycache__" -prune -exec rm -rf {} +

# The server runs as root only so that every agent tool call and project script can
# run as the unprivileged "sandbox" user, which cannot read the server's environment
# (where ANTHROPIC_API_KEY lives).
ENV HARNESS_SANDBOX_USER=sandbox \
    HARNESS_RUNS_DIR=/app/harness/runs \
    PYTHONUNBUFFERED=1 \
    PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn harness.app:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
