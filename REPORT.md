# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

**Question 1: "What is the agentic loop?"**

The **agentic loop** is the core cycle that an AI agent follows to accomplish tasks autonomously. It's the fundamental pattern of how agents like me operate. Here's the typical loop:

1. **Perceive** — Receive input from the user or environment (a question, a command, sensor data, etc.)
2. **Reason/Plan** — Analyze the input, understand intent, and decide what to do next. This includes:
   - Breaking down complex tasks into steps
   - Choosing which tools or actions to use
   - Determining if more information is needed
3. **Act** — Execute the chosen action(s):
   - Call tools (read files, run commands, search the web, etc.)
   - Make API calls
   - Modify files or systems
4. **Observe** — Receive the results of those actions (tool outputs, errors, new data)
5. **Reflect/Iterate** — Evaluate the results:
   - Did the action succeed?
   - Is the task complete, or is another step needed?
   - If not done, go back to step 2 (Reason/Plan) with the new information
6. **Respond** — Once the task is complete, deliver the final answer or result to the user

This loop enables agents to handle multi-step tasks, adapt to failures, chain reasoning outputs, and work autonomously.

**Question 2: "What labs are available in our LMS?"**

The agent returned real lab names from the backend because the MCP LMS tools were already configured in the nanobot config.json:

1. Lab 01 – Products, Architecture & Roles
2. Lab 02 — Run, Fix, and Deploy a Backend Service
3. Lab 03 — Backend API: Explore, Debug, Implement, Deploy
4. Lab 04 — Testing, Front-end, and AI Agents
5. Lab 05 — Data Pipeline and Analytics Dashboard
6. Lab 06 — Build Your Own Agent
7. Lab 07 — Build a Client with an AI Coding Agent
8. Lab 08 — lab-08

## Task 1B — Agent with LMS tools

**Question 1: "What labs are available?"**

Here are the available labs:

1. Lab 01 – Products, Architecture & Roles
2. Lab 02 — Run, Fix, and Deploy a Backend Service
3. Lab 03 — Backend API: Explore, Debug, Implement, Deploy
4. Lab 04 — Testing, Front-end, and AI Agents
5. Lab 05 — Data Pipeline and Analytics Dashboard
6. Lab 06 — Build Your Own Agent
7. Lab 07 — Build a Client with an AI Coding Agent
8. Lab 08 — lab-08

Let me know if you'd like to see scores, pass rates, completion rates, group performance, or submission timelines for any specific lab!

**Question 2: "Is the LMS backend healthy?"**

The agent called the `mcp_lms_lms_health` tool and returned: "Yes, the LMS backend is healthy! It currently has 56 items in the system."

## Task 1C — Skill prompt

**Question: "Show me the scores" (without specifying a lab)**

The agent followed the LMS skill strategy:

1. First called `mcp_lms_lms_labs` to get available labs
2. Used the structured-ui skill to present a choice to the user
3. Asked which lab the user wants to see scores for

Response:
> Which lab would you like to see scores for?
>
> 1. Lab 01 – Products, Architecture & Roles
> 2. Lab 02 — Run, Fix, and Deploy a Backend Service
> 3. Lab 03 — Backend API: Explore, Debug, Implement, Deploy
> 4. Lab 04 — Testing, Front-end, and AI Agents
> 5. Lab 05 — Data Pipeline and Analytics Dashboard
> 6. Lab 06 — Build Your Own Agent
> 7. Lab 07 — Build a Client with an AI Coding Agent
> 8. lab-08

This demonstrates the skill prompt is working - the agent asks for clarification when a lab parameter is missing.

## Task 2A — Deployed agent

<!-- Paste a short nanobot startup log excerpt showing the gateway started inside Docker -->

## Task 2B — Web client

<!-- Screenshot of a conversation with the agent in the Flutter web app -->

## Task 3A — Structured logging

<!-- Paste happy-path and error-path log excerpts, VictoriaLogs query screenshot -->

## Task 3B — Traces

<!-- Screenshots: healthy trace span hierarchy, error trace -->

## Task 3C — Observability MCP tools

<!-- Paste agent responses to "any errors in the last hour?" under normal and failure conditions -->

## Task 4A — Multi-step investigation

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

## Task 4C — Bug fix and recovery

<!-- 1. Root cause identified
     2. Code fix (diff or description)
     3. Post-fix response to "What went wrong?" showing the real underlying failure
     4. Healthy follow-up report or transcript after recovery -->
