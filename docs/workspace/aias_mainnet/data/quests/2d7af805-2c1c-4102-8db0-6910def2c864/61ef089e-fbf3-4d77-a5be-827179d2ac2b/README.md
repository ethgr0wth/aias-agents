# Decision Engine for Automated Follow-Up and Human Escalation

This project is a lead decision engine that decides whether to:

- send an automated follow-up
- wait before contacting again
- escalate to human outreach

It also tracks lead status in a local CSV file so you have simple spreadsheet-compatible reporting.

## Features

- Uses the AiAS chat completions API
- Produces structured JSON decisions
- Includes deterministic rule overrides for safety and consistency
- Escalates high-value, high-intent, or sensitive leads to humans
- Falls back gracefully if the API is unavailable
- Writes and updates lead records in `lead_status.csv`

## Configuration

Set your API key before running:

```bash
export AIASSIST_API_KEY="aai_your_real_key"
```

Optional environment variables:

```bash
export AIASSIST_MODEL="llama-3.3-70b-versatile"
export AIASSIST_AGENT_ID="your-agent-id"
export LEAD_CSV_PATH="lead_status.csv"
```

## Run

```bash
python snippet_1774430016164.py
```

## CSV Tracking

Each run updates a local CSV with one row per lead. The file includes:

- lead identity fields
- lifecycle stage
- lead status
- decision
- priority
- follow-up channel
- wait days
- reason
- human escalation reason
- next best action
- last updated timestamp

Lead status values are mapped from decisions:

- `automated_followup` -> `followup_scheduled`
- `wait` -> `waiting`
- `human_outreach` -> `escalated_to_human`

## Output

- JSON printed to stdout
- CSV written locally for spreadsheet tracking