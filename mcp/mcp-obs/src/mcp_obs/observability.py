"""MCP observability client for VictoriaLogs and VictoriaTraces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class Settings:
    """Observability settings resolved from environment variables."""

    victorialogs_url: str
    victoriatraces_url: str

    @classmethod
    def from_env(cls) -> Settings:
        import os

        vl_url = os.environ.get("NANOBOT_VICTORIALOGS_URL", "")
        vt_url = os.environ.get("NANOBOT_VICTORIATRACES_URL", "")

        if not vl_url:
            raise RuntimeError(
                "NANOBOT_VICTORIALOGS_URL is not set. "
                "Set it to the VictoriaLogs base URL (e.g. http://victorialogs:9428)."
            )
        if not vt_url:
            raise RuntimeError(
                "NANOBOT_VICTORIATRACES_URL is not set. "
                "Set it to the VictoriaTraces base URL (e.g. http://victoriatraces:10428)."
            )

        return cls(victorialogs_url=vl_url, victoriatraces_url=vt_url)


class ObservabilityClient:
    """HTTP client for VictoriaLogs and VictoriaTraces APIs."""

    def __init__(
        self,
        victorialogs_url: str,
        victoriatraces_url: str,
        httpx_client: httpx.AsyncClient | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._vl_base = victorialogs_url.rstrip("/")
        self._vt_base = victoriatraces_url.rstrip("/")
        self._client = httpx_client or httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    # --- VictoriaLogs (LogsQL query API) ---

    async def search_logs(
        self,
        query: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search VictoriaLogs using a LogsQL query."""
        url = f"{self._vl_base}/select/logsql/query"
        params: dict[str, Any] = {"query": query, "limit": limit}
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        # VictoriaLogs returns NDJSON (one JSON object per line)
        lines = resp.text.strip().splitlines()
        results: list[dict[str, Any]] = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    results.append({"_raw": line})
        return results

    async def count_errors(
        self,
        service: str | None = None,
        minutes: int = 60,
    ) -> dict[str, Any]:
        """Count error-level log entries over a time window.

        If *service* is given the query is scoped to that service name.
        """
        time_filter = f"_time:{minutes}m"
        severity_filter = "severity:ERROR"
        parts = [time_filter, severity_filter]
        if service:
            parts.append(f'service.name:"{service}"')
        query = " ".join(parts)

        url = f"{self._vl_base}/select/logsql/query"
        params: dict[str, Any] = {"query": query, "limit": 10000}
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        lines = resp.text.strip().splitlines()
        count = sum(1 for l in lines if l.strip())

        # Also gather per-service breakdown
        services: dict[str, int] = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                svc_name: str = obj.get("service.name", "unknown")
                services[svc_name] = services.get(svc_name, 0) + 1
            except json.JSONDecodeError:
                pass

        return {
            "total_errors": count,
            "time_window_minutes": minutes,
            "service_filter": service,
            "per_service": services,
        }

    # --- VictoriaTraces (Jaeger-compatible API) ---

    async def list_traces(
        self,
        service: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List recent traces from VictoriaTraces."""
        url = f"{self._vt_base}/select/jaeger/api/traces"
        params: dict[str, Any] = {"limit": limit}
        if service:
            params["service"] = service
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        # The Jaeger-compatible API returns {"data": [...]}
        return data.get("data", [])

    async def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        """Fetch a single trace by ID."""
        url = f"{self._vt_base}/select/jaeger/api/traces/{trace_id}"
        resp = await self._client.get(url)
        resp.raise_for_status()
        data = resp.json()
        traces = data.get("data", [])
        if traces:
            return traces[0]
        return None
