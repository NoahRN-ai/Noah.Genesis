# Noah Agent Prompt Documentation

This document outlines the various prompts used by the Noah agent for different tasks. Centralizing these prompts helps in maintaining clarity, consistency, and ease of updates.

## RAG Information Retrieval Prompts (Task 3.3.A)

[Prompts to be added/consolidated here]

## Note Drafting & Handoff Report Prompts (Task 3.3.B)

[Prompts to be added/consolidated here]

## Patient-Friendly Summaries (Task 3.3.C)

This section contains prompts designed to help the Noah agent generate patient-friendly summaries of their health data logs.

### Prompt 1: Summary of a Single Recent Patient Data Log

**Purpose:** To generate a concise, patient-friendly summary of a single, recent `PatientDataLog` entry. This is typically used when the patient asks about their latest reading or a specific recent event.

**When to use:** When a patient inquires about their most recent data point (e.g., "What was my last blood pressure reading?") or a specific log entry.

**Prompt:**

```
You are a helpful medical assistant AI. A patient has shared a new health data log with you.
Please provide a brief, patient-friendly summary of the following health data log entry.
Focus on the key information and explain any medical terms in simple language.
Avoid medical jargon where possible, or explain it clearly if necessary.
The goal is to make this information understandable and actionable for the patient.

Log Entry Data:
{log_entry_data}

Please provide your summary:
```

**Placeholders:**

*   `{log_entry_data}`: This placeholder will be replaced with the actual data from a single `PatientDataLog` object. This data typically includes the type of measurement (e.g., blood pressure, glucose level), the value, units, and the timestamp. For example:
    ```json
    {
      "log_id": "some_uuid",
      "timestamp": "2023-10-27T10:30:00Z",
      "data_type": "blood_pressure",
      "content": {
        "systolic": 120,
        "diastolic": 80,
        "unit": "mmHg"
      },
      "source": "PatientApp",
      "created_at": "2023-10-27T10:31:00Z"
    }
    ```

### Prompt 2: Summary of Multiple Recent Patient Data Logs or a Trend

**Purpose:** To generate a patient-friendly summary of multiple recent `PatientDataLog` entries, potentially identifying a trend or pattern if one exists.

**When to use:** When a patient asks for a summary of their recent activity (e.g., "How have my blood sugar levels been this week?") or when a series of related logs might indicate a trend.

**Prompt:**

```
You are a helpful medical assistant AI. A patient has shared their recent health data logs with you.
Please provide a brief, patient-friendly summary of the following health data log entries.
If you notice any apparent trends (e.g., consistently high readings, improvements, stability), please mention them in simple terms.
Focus on the key information and explain any medical terms in simple language.
Avoid medical jargon where possible, or explain it clearly if necessary.
The goal is to make this information understandable and actionable for the patient.

Log Entries Data:
{log_entries_data}

Please provide your summary, and mention any noticeable patterns or trends if applicable:
```

**Placeholders:**

*   `{log_entries_data}`: This placeholder will be replaced with a list of recent `PatientDataLog` objects. Each object in the list will have a similar structure to the `log_entry_data` described in Prompt 1. For example:
    ```json
    [
      {
        "log_id": "uuid1",
        "timestamp": "2023-10-27T08:00:00Z",
        "data_type": "blood_glucose",
        "content": {"value": 95, "unit": "mg/dL"},
        "source": "GlucometerX",
        "created_at": "2023-10-27T08:01:00Z"
      },
      {
        "log_id": "uuid2",
        "timestamp": "2023-10-26T18:30:00Z",
        "data_type": "blood_glucose",
        "content": {"value": 105, "unit": "mg/dL"},
        "source": "GlucometerX",
        "created_at": "2023-10-26T18:31:00Z"
      },
      {
        "log_id": "uuid3",
        "timestamp": "2023-10-25T07:45:00Z",
        "data_type": "blood_glucose",
        "content": {"value": 90, "unit": "mg/dL"},
        "source": "GlucometerX",
        "created_at": "2023-10-25T07:46:00Z"
      }
    ]
    ```
```
