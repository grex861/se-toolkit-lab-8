---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

You have access to LMS (Learning Management System) MCP tools that provide live course data. Use these tools to answer questions about labs, learners, scores, and performance metrics.

## Available Tools

- **lms_health**: Check if the LMS backend is healthy. Returns item count. Use when asked about system status.
- **lms_labs**: List all available labs. Use when the user asks about labs without specifying which one, or when you need lab identifiers.
- **lms_learners**: List all registered learners. Use when asked about student enrollment.
- **lms_pass_rates**: Get pass rates (avg score and attempt count per task) for a specific lab. Requires `lab` parameter.
- **lms_timeline**: Get submission timeline (date + submission count) for a specific lab. Requires `lab` parameter.
- **lms_groups**: Get group performance (avg score + student count per group) for a specific lab. Requires `lab` parameter.
- **lms_top_learners**: Get top learners by average score for a specific lab. Requires `lab` parameter, optional `limit` (default 5).
- **lms_completion_rate**: Get completion rate (passed / total) for a specific lab. Requires `lab` parameter.
- **lms_sync_pipeline**: Trigger the LMS sync pipeline. Use when data appears stale or when explicitly requested.

## Strategy

### When the user asks about scores, pass rates, completion, groups, timeline, or top learners:

1. **If a lab is specified**: Call the relevant tool directly with that lab identifier.

2. **If no lab is specified**:
   - First call `lms_labs` to get available labs
   - Then use the `structured-ui` skill to present a choice to the user
   - For `choice` type, use each lab's `title` field as the label and `id` field as the value
   - Wait for the user to select a lab before proceeding

### Example flow for "Show me the scores":

1. Call `lms_labs` to get the list of labs
2. Present a choice UI with lab titles as labels and lab IDs as values
3. After user selects, call `lms_pass_rates` with the selected lab

### Formatting results:

- **Percentages**: Format as "X%" (e.g., "75%" not "0.75")
- **Scores**: Show with one decimal place if needed (e.g., "8.5/10")
- **Counts**: Use plain numbers (e.g., "120 submissions")
- **Dates**: Use readable format (e.g., "2024-01-15")

### Response style:

- Keep responses concise and focused on the data
- When presenting multiple metrics, use bullet points or a table format
- If the backend is unhealthy or returns empty data, explain what you tried and suggest running the sync pipeline

### When asked "what can you do?":

Explain that you can:
- Check LMS backend health
- List available labs and learners
- Show pass rates, completion rates, and submission timelines for specific labs
- Show group performance and top learners per lab
- Trigger the sync pipeline to refresh data

Be clear about what requires a lab parameter and that you'll ask for clarification if not provided.
