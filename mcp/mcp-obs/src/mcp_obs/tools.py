"""MCP tool definitions for observability (VictoriaLogs + VictoriaTraces)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from mcp.types import Tool
from pydantic import BaseModel, Field

from mcp_obs.observability import ObservabilityClient


# --- Pydantic argument models ---

class NoArgs(BaseModel):
    """Empty input model for tools that only need server-side configuration."""


class LogsSearchQuery(BaseModel):
    query: str = Field(
        description="LogsQL query string. Examples: "
        "'_time:10m severity:ERROR', "
        "'_time:1h service.name:\"Learning Management Service\" severity:ERROR'."
    )
    limit: int = Field(
        default=50,
        description="Maximum number of log entries to return (default 50)."
    )


class LogsErrorCountQuery(BaseModel):
    service: str = Field(
        default="",
        description="Service name to filter errors. Leave empty for all services."
    )
    minutes: int = Field(
        default=60,
        description="Time window in minutes to look back for errors (default 60)."
    )


class TracesListQuery(BaseModel):
    service: str = Field(
        default="",
        description="Service name to filter traces. Leave empty for all services."
    )
    limit: int = Field(
        default=20,
        description="Maximum number of traces to return (default 20)."
    )


class TracesGetQuery(BaseModel):
    trace_id: str = Field(
        description="The trace ID to fetch. Must be a valid hex trace ID from logs or traces_list."
    )


# --- Payload type and handler signature ---

ToolPayload = str
ToolHandler = Callable[[ObservabilityClient, BaseModel], Awaitable[ToolPayload]]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Wraps a tool's name, description, argument model, and handler."""

    name: str
    description: str
    model: type[BaseModel]
    handler: ToolHandler

    def as_tool(self) -> Tool:
        schema = self.model.model_json_schema()
        schema.pop("$defs", None)
        schema.pop("title", None)
        return Tool(name=self.name, description=self.description, inputSchema=schema)


# --- Tool handlers ---

async def _logs_search(
    client: ObservabilityClient,
    args: BaseModel,
) -> ToolPayload:
    """Search VictoriaLogs with a LogsQL query."""
    query = args if isinstance(args, LogsSearchQuery) else LogsSearchQuery.model_validate(args)
    results = await client.search_logs(query=query.query, limit=query.limit)
    if not results:
        return "No log entries found matching your query."

    # Summarize instead of dumping raw JSON
    output = [f"Found {len(results)} log entries for query: `{query.query}`\n"]
    for entry in results[:query.limit]:
        ts = entry.get("_time", entry.get("timestamp", "unknown"))
        severity = entry.get("severity", entry.get("level", "unknown"))
        event = entry.get("event", entry.get("_msg", ""))
        svc: str = entry.get("service.name", "unknown")
        trace_id: str = entry.get("trace_id", "")
        summary = f"[{ts}] {severity} {svc}/{event}"
        if trace_id:
            summary += f" trace={trace_id[:16]}..."
        output.append(summary)

        # Include error message if present
        if str(severity).upper() in ("ERROR", "CRITICAL", "FATAL"):
            exc_msg = entry.get("exception.message", entry.get("error", ""))
            if exc_msg:
                output.append(f"  Error: {exc_msg}")

    if len(results) > query.limit:
        output.append(f"\n... and {len(results) - query.limit} more entries.")

    return "\n".join(output)


async def _logs_error_count(
    client: ObservabilityClient,
    args: BaseModel,
) -> ToolPayload:
    """Count error-level log entries over a time window."""
    query = args if isinstance(args, LogsErrorCountQuery) else LogsErrorCountQuery.model_validate(args)
    svc = query.service if query.service else None
    result = await client.count_errors(service=svc, minutes=query.minutes)

    lines = [
        f"Error count (last {result['time_window_minutes']} minutes):",
        f"  Total errors: {result['total_errors']}",
    ]
    if result.get("service_filter"):
        lines[0] += f" for service '{result['service_filter']}'"

    if result.get("per_service"):
        lines.append("  Breakdown by service:")
        for svc_name, count in sorted(
            result["per_service"].items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"    {svc_name}: {count}")

    return "\n".join(lines)


async def _traces_list(
    client: ObservabilityClient,
    args: BaseModel,
) -> ToolPayload:
    """List recent traces from VictoriaTraces."""
    query = args if isinstance(args, TracesListQuery) else TracesListQuery.model_validate(args)
    svc = query.service if query.service else None
    traces = await client.list_traces(service=svc, limit=query.limit)

    if not traces:
        msg = "No traces found"
        if svc:
            msg += f" for service '{svc}'"
        return msg

    output = [f"Found {len(traces)} recent traces" + (f" for '{svc}'" if svc else "") + ":\n"]
    for trace in traces[:query.limit]:
        trace_id = trace.get("traceID", trace.get("traceId", "unknown"))
        start_time = trace.get("startTime", "unknown")
        duration_us = trace.get("duration", 0)
        duration_ms = duration_us / 1000 if duration_us else 0
        span_count = len(trace.get("spans", []))
        output.append(f"  trace_id={trace_id}  started={start_time}  duration={duration_ms:.1f}ms  spans={span_count}")

    return "\n".join(output)


async def _traces_get(
    client: ObservabilityClient,
    args: BaseModel,
) -> ToolPayload:
    """Fetch a specific trace by ID and show its span hierarchy."""
    query = args if isinstance(args, TracesGetQuery) else TracesGetQuery.model_validate(args)
    trace = await client.get_trace(query.trace_id)
    if not trace:
        return f"No trace found with ID: {query.trace_id}"

    trace_id = trace.get("traceID", trace.get("traceId", query.trace_id))
    start_time = trace.get("startTime", "unknown")
    duration_us = trace.get("duration", 0)
    duration_ms = duration_us / 1000 if duration_us else 0
    spans = trace.get("spans", [])

    output = [
        f"Trace {trace_id}",
        f"  Started: {start_time}",
        f"  Duration: {duration_ms:.1f}ms",
        f"  Spans: {len(spans)}",
        "",
        "Span hierarchy:",
    ]

    for span in spans:
        op = span.get("operationName", "unknown")
        svc: str = span.get("serviceName", "unknown")
        dur_us = span.get("duration", 0)
        dur_ms = dur_us / 1000 if dur_us else 0
        depth = span.get("depth", 0)
        indent = "  " * (depth + 1)

        # Check for error tags
        has_error = False
        for tag in span.get("tags", []):
            if tag.get("key") == "error" and tag.get("value") in (True, "true", 1):
                has_error = True
                break

        error_marker = " [ERROR]" if has_error else ""
        output.append(f"{indent}[{svc}] {op} ({dur_ms:.1f}ms){error_marker}")

        # Show logs for error spans
        if has_error:
            for log in span.get("logs", []):
                for field in log.get("fields", []):
                    if field.get("key") == "error" or field.get("key") == "error.object":
                        output.append(f"{indent}  -> {field.get('value', '')}")

    return "\n".join(output)


# --- Registry ---

TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="obs_logs_search",
        description="Search structured logs in VictoriaLogs using a LogsQL query. "
        "Use filters like '_time:10m severity:ERROR service.name:\"Learning Management Service\"'. "
        "Use this when the user asks about specific log events or wants to search logs by keyword.",
        model=LogsSearchQuery,
        handler=_logs_search,
    ),
    ToolSpec(
        name="obs_logs_error_count",
        description="Count error-level log entries over a time window. "
        "Optionally filter by service name. "
        "Use this first when the user asks 'any errors?' to quickly see if there are recent errors.",
        model=LogsErrorCountQuery,
        handler=_logs_error_count,
    ),
    ToolSpec(
        name="obs_traces_list",
        description="List recent traces from VictoriaTraces. "
        "Optionally filter by service name. "
        "Use this when the user wants to see recent request traces or find a specific trace.",
        model=TracesListQuery,
        handler=_traces_list,
    ),
    ToolSpec(
        name="obs_traces_get",
        description="Fetch a specific trace by ID and display its span hierarchy. "
        "Use this after finding a trace_id in logs or traces_list to inspect the full request flow.",
        model=TracesGetQuery,
        handler=_traces_get,
    ),
)

TOOLS_BY_NAME: dict[str, ToolSpec] = {ts.name: ts for ts in TOOL_SPECS}
