#!/usr/bin/env python
"""Resolve environment variables into nanobot config, then launch `nanobot gateway`.

Docker passes secrets via environment variables, not by editing files.
This script:
1. Reads config.json
2. Overrides fields that must come from Docker env vars
3. Writes config.resolved.json
4. execvp() into `nanobot gateway`
"""

import json
import os
import sys
from pathlib import Path


def resolve_config() -> str:
    """Read config.json, inject env vars, return path to resolved config."""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    # LLM provider settings
    if llm_api_key := os.environ.get("LLM_API_KEY"):
        config["providers"]["custom"]["apiKey"] = llm_api_key
    if llm_api_base_url := os.environ.get("LLM_API_BASE_URL"):
        config["providers"]["custom"]["apiBase"] = llm_api_base_url
    if llm_api_model := os.environ.get("LLM_API_MODEL"):
        config["agents"]["defaults"]["model"] = llm_api_model

    # Gateway settings
    if gateway_host := os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS"):
        config["gateway"]["host"] = gateway_host
    if gateway_port := os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT"):
        config["gateway"]["port"] = int(gateway_port)

    # Webchat channel settings
    if webchat_host := os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS"):
        config.setdefault("channels", {})
        config["channels"].setdefault("webchat", {})
        config["channels"]["webchat"]["host"] = webchat_host
    if webchat_port := os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT"):
        config["channels"].setdefault("webchat", {})
        config["channels"]["webchat"]["port"] = int(webchat_port)

    # Enable the webchat channel if the env var is present
    if os.environ.get("NANOBOT_WEBCHAT_ENABLED"):
        config.setdefault("channels", {})
        config["channels"]["webchat"] = {
            "enabled": True,
            "allowFrom": ["*"],
        }
        if webchat_host := os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS"):
            config["channels"]["webchat"]["host"] = webchat_host
        if webchat_port := os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT"):
            config["channels"]["webchat"]["port"] = int(webchat_port)

    # MCP server environment vars for LMS
    if backend_url := os.environ.get("NANOBOT_LMS_BACKEND_URL"):
        config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = backend_url
    if lms_api_key := os.environ.get("NANOBOT_LMS_API_KEY"):
        config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = lms_api_key

    # MCP server for webchat (structured UI delivery)
    # The relay runs inside the same container, so use localhost.
    if os.environ.get("NANOBOT_WEBCHAT_MCP_ENABLED"):
        relay_port = os.environ.get("NANOBOT_WEBCHAT_RELAY_PORT", "8766")
        ui_relay_token = os.environ.get("NANOBOT_ACCESS_KEY", "")
        config["tools"]["mcpServers"]["webchat"] = {
            "command": "python",
            "args": ["-m", "mcp_webchat"],
            "env": {
                "NANOBOT_UI_RELAY_URL": f"http://127.0.0.1:{relay_port}",
                "NANOBOT_UI_RELAY_TOKEN": ui_relay_token,
            },
        }

    # Write resolved config next to the original
    config_dir = Path(__file__).parent
    resolved_path = config_dir / "config.resolved.json"
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    return str(resolved_path)


def main():
    workspace_dir = Path(__file__).parent / "workspace"
    resolved_config = resolve_config()

    print(f"Using config: {resolved_config}")
    print(f"Using workspace: {workspace_dir}")

    # Build command: nanobot gateway --config <resolved> --workspace <workspace>
    cmd = ["nanobot", "gateway", "--config", resolved_config, "--workspace", str(workspace_dir)]
    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    main()
