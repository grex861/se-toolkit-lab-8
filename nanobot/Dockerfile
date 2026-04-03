# Multi-stage uv build for nanobot gateway.
# Uses the root workspace context to resolve all dependencies.

# ---
# Stage 1: build the application
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy root workspace files.
COPY --from=workspace pyproject.toml uv.lock /app/

# Copy all packages needed by the workspace.
COPY --from=workspace backend/pyproject.toml /app/backend/pyproject.toml
COPY --from=workspace qwen-code-api/pyproject.toml /app/qwen-code-api/pyproject.toml
COPY --from=workspace mcp/mcp-lms/pyproject.toml /app/mcp/mcp-lms/pyproject.toml
COPY --from=workspace mcp/mcp-lms/src/ /app/mcp/mcp-lms/src/
COPY --from=workspace mcp/mcp-obs/pyproject.toml /app/mcp/mcp-obs/pyproject.toml
COPY --from=workspace mcp/mcp-obs/src/ /app/mcp/mcp-obs/src/
COPY --from=workspace nanobot/pyproject.toml /app/nanobot/pyproject.toml
COPY --from=workspace nanobot-websocket-channel/nanobot-channel-protocol/ /app/nanobot-websocket-channel/nanobot-channel-protocol/
COPY --from=workspace nanobot-websocket-channel/nanobot-webchat/ /app/nanobot-websocket-channel/nanobot-webchat/
COPY --from=workspace nanobot-websocket-channel/mcp-webchat/ /app/nanobot-websocket-channel/mcp-webchat/

# Sync from the workspace root, installing only the nanobot package and its deps.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace --package nanobot

# Copy nanobot source and workspace files
COPY --from=workspace nanobot/main.py /app/nanobot/main.py
COPY --from=workspace nanobot/entrypoint.py /app/nanobot/entrypoint.py
COPY --from=workspace nanobot/README.md /app/nanobot/README.md
COPY --from=workspace nanobot/config.json /app/nanobot/config.json
COPY --from=workspace nanobot/workspace/ /app/nanobot/workspace/

# Final sync to pick up the nanobot package itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package nanobot

# ---
# Stage 2: final image
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

ARG APP_UID=1000
ARG APP_GID=1000

RUN groupadd --system --gid ${APP_GID} appuser \
    && useradd --system --gid ${APP_GID} --uid ${APP_UID} --create-home appuser

# Copy the built application
COPY --from=builder --chown=appuser:appuser /app /app

RUN mkdir -p /app/nanobot/workspace && chown -R appuser:appuser /app/nanobot/workspace

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
USER appuser

CMD ["python", "/app/nanobot/entrypoint.py"]
