# Observability Skill

When the user asks about system health, errors, logs, traces, or anything observability-related, use the observability MCP tools to investigate and report findings.

## Available Tools

- **`obs_logs_error_count`** — Count error-level log entries over a time window. Use this *first* when the user asks "any errors?" to quickly see whether there are recent errors and which services are affected.
- **`obs_logs_search`** — Search structured logs in VictoriaLogs using a LogsQL query. Use this to inspect specific log events, find trace IDs, or search by keyword.
- **`obs_traces_list`** — List recent traces from VictoriaTraces. Use this to see recent request flows or find a trace ID.
- **`obs_traces_get`** — Fetch a specific trace by ID and show its span hierarchy. Use this after finding a trace_id in logs to inspect the full request flow.

## Reasoning Strategy

1. **Quick scan first**: When asked "any errors?" or "is anything broken?", call `obs_logs_error_count` with a narrow time window (e.g., 10 minutes) and the relevant service name (e.g., "Learning Management Service"). This gives a fast yes/no answer.

2. **Investigate details**: If errors are found, use `obs_logs_search` with a query like `_time:10m service.name:"Learning Management Service" severity:ERROR` to see the actual error messages. Extract any `trace_id` from the log entries.

3. **Follow the trace**: If you found a `trace_id`, call `obs_traces_get` with that ID to show the full request flow. Point out which span failed and why.

4. **Summarize, don't dump**: Give a short, readable summary. Do NOT dump raw JSON. Example:
   - ✅ "Found 3 errors in the LMS backend over the last 10 minutes. All are database connection failures caused by PostgreSQL being unreachable. Trace `a1b2c3...` shows the request failed at the `db_query` step after 500ms."
   - ❌ (Pasting 200 lines of JSON log entries)

## Query Tips

- VictoriaLogs field names: `service.name`, `severity`, `event`, `trace_id`
- Time filter syntax: `_time:10m`, `_time:1h`, `_time:30m`
- Severity filter: `severity:ERROR`
- Service filter: `service.name:"Learning Management Service"`
- Example query: `_time:10m service.name:"Learning Management Service" severity:ERROR`

## When to Use This Skill

- User asks: "any errors in the last hour?"
- User asks: "what went wrong?"
- User asks: "check system health"
- User asks about a specific service's errors
- User asks to investigate a failure

## When NOT to Use This Skill

- User asks about LMS data (labs, scores, learners) — use the LMS skill instead
- User asks general knowledge questions — answer directly
- User asks about code or files — use your built-in tools
