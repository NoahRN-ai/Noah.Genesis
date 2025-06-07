# GCP Logging & Monitoring Setup Details (terraform/monitoring_logging.tf)

This document describes the logging export strategy and the initial Cloud Monitoring dashboard configuration for Project Noah MVP V1.0, as defined in `terraform/monitoring_logging.tf`.

## 1. Logging Exports (Sinks)

The configuration for logging exports (sinks) utilizes several parameters defined as local variables within the `monitoring_logging.tf` file. These include `log_archive_bucket_name_suffix` (defaulting to an empty string), `log_archive_retention_period_days` (defaulting to 2190 days, or 6 years), `bigquery_log_dataset_id` (defaulting to "noah_mvp_logs_analysis"), and `bigquery_log_dataset_location` (defaulting to "US"). These defaults can be overridden if necessary.

A dual-destination strategy is implemented for project logs to support both long-term archival and operational analysis:

### 1.1. Log Sink to Cloud Storage (`google_logging_project_sink.noah_mvp_gcs_log_sink`)

*   **Purpose:** Long-term archival of logs. This is crucial for compliance (e.g., HIPAA which may require retention for 6 years or more) and historical forensic analysis.
*   **Destination Bucket:** `bkt-noah-mvp-logs-archive-${google_project.noah_mvp_project.project_id}${var.log_archive_bucket_name_suffix}` (created by Terraform).
*   **Filter:** `severity >= DEFAULT` (captures default severity logs and higher). This provides a comprehensive archive.
*   **Storage Class & Retention:**
    *   Logs are initially written with `STANDARD` storage class.
    *   Lifecycle rules automatically transition logs to:
        *   `NEARLINE` after 30 days.
        *   `COLDLINE` after 90 days.
    *   Logs are **deleted** after `var.log_archive_retention_period_days` (defaulting to 2190 days / 6 years). This should be reviewed against specific compliance requirements.
*   **Permissions:** The sink uses a unique `writer_identity` (a dedicated service account) which is granted `roles/storage.objectCreator` on the archive bucket.

### 1.2. Log Sink to BigQuery (`google_logging_project_sink.noah_mvp_bq_log_sink`)

*   **Purpose:** Facilitates advanced analysis, querying, and visualization of log data using SQL.
*   **Destination Dataset:** ID `var.bigquery_log_dataset_id` (default 'noah_mvp_logs_analysis') in project `google_project.noah_mvp_project.project_id`, location `var.bigquery_log_dataset_location` (default "US"). Created by Terraform.
*   **Filter:** `severity >= INFO` (captures informational logs and higher). This focuses the analytical dataset on more significant events, potentially reducing BigQuery storage and query costs compared to exporting all logs.
*   **Permissions:** The sink uses a unique `writer_identity` granted `roles/bigquery.dataEditor` on the destination dataset, allowing it to create tables and write log entries.
*   **Table Partitioning:** Log exports to BigQuery automatically create date-partitioned tables, which is beneficial for query performance and cost management.

## 2. Cloud Monitoring Dashboard (`google_monitoring_dashboard.noah_mvp_overview_dashboard`)

An initial dashboard named "Noah MVP - Core Services Overview" is provisioned to provide at-a-glance visibility into the health and performance of key MVP services.

*   **Purpose:** Early detection of issues, performance monitoring, and understanding resource utilization for core services.
*   **Key Metrics Displayed (Example Widgets):**
    *   **Cloud Run - AI Agent Service (Assumed service name: `noah-mvp-agent-service` - **UPDATE IF DIFFERENT**):**
        *   Request Count (Sum over time)
        *   5XX Error Count (Sum over time, indicating server-side issues)
        *   *(Further widgets like Request Latency, CPU/Memory Utilization can be added)*
    *   **Cloud Run - WebApp Service (Assumed service name: `noah-mvp-webapp-service` - **UPDATE IF DIFFERENT**):**
        *   *(Similar metrics as AI Agent can be added here: Request Count, Error Count, Latency)*
    *   **Firestore:**
        *   Document Read Operations (Sum over time)
        *   *(Further widgets like Write Operations, Operation Latencies can be added)*
    *   **Vertex AI Endpoints (LLM Serving):**
        *   Prediction Request Count (Project Total - can be filtered by specific `endpoint_id` once known)
        *   *(Further widgets like Prediction Error Count, Latencies, Accelerator Utilization can be added)*
*   **Structure:** The dashboard uses a `gridLayout`. The provided Terraform includes a basic JSON structure. This can be extended by adding more widgets directly in the Terraform HCL or by designing the dashboard in the GCP Console and exporting its JSON representation.
*   **Note on Dynamic Identifiers:** Dashboard widget filters may require specific resource names (e.g., Cloud Run service name, Vertex AI Endpoint ID). The example uses placeholders or broad filters. These should be updated with actual deployed resource names/IDs for precise monitoring.

## 3. Suggested Alert Policies (`dynamous.ai` Contribution)

While only one example alert policy (`cloud_run_agent_5xx_error_alert`) is implemented in Terraform for MVP brevity, the following critical alert policies are recommended for an AI-driven application like Project Noah:

### 3.1. Cloud Run Services (AI Agent & WebApp)
*   **High 5XX Error Rate:** Alert when the rate of 5xx server errors exceeds a threshold (e.g., > 1-5% of requests over a 5-10 minute window). (Example implemented)
*   **High Request Latency:** Alert when p95 or p99 request latency consistently exceeds a defined SLO (e.g., > 2 seconds for API calls).
*   **Container Crashes / High Restart Rate:** If using `run.googleapis.com/container/instance_count` and observing frequent dips or restarts.

### 3.2. Firestore Database
*   **High Operation Latency:** Alert when read/write operation latencies (e.g., p95) for Firestore exceed acceptable thresholds.
*   **High Error Rate (if specific error metrics available):** Monitor for any significant increase in errors returned by Firestore.

### 3.3. Vertex AI Endpoints (LLM)
*   **High Prediction Error Rate:** Alert if the percentage of failed prediction requests to an LLM endpoint is high.
*   **High Prediction Latency:** Alert if the p95/p99 latency for LLM predictions is consistently above SLOs.
*   **Quota Issues:** Monitor for `quota/limit` errors if requests are being throttled.
*   **(AI-Specific) Low Model Utility/Accuracy:** If custom metrics can be exported from the application indicating poor AI responses (e.g., high rate of "I don't know" from the agent, low RAG retrieval relevance score if measurable), set alerts on these. This is more advanced.
*   **(AI-Specific) High Token Usage (Cost Control):** If Vertex AI exposes metrics for token consumption per request/period for the specific models used, an alert on unusually high token usage could indicate runaway behavior or inefficient prompting.

### 3.4. Logging & Sink Health
*   **Log Sink Errors:** Alert if `logging.googleapis.com/exports/error_count` for the defined sinks shows persistent errors, indicating logs are not being exported correctly.
*   **BigQuery Ingestion Delays/Errors:** Monitor `bigquery.googleapis.com/storage/write_api_request_count` with error status if available for sink destination.

**Implementation Notes for Alerts:**
*   Alert policies should be configured with appropriate notification channels (e.g., email, PagerDuty, Slack) to ensure timely response from the AEM team.
*   Thresholds should be tuned based on observed baseline performance and desired SLOs.

## 4. `dynamous.ai` Contributions to Monitoring & Logging

*   **HIPAA-Compliant Archival:** Advocating for long-term log archival with appropriate storage classes in Cloud Storage.
*   **Actionable Analytics:** Setting up a BigQuery sink for structured log analysis.
*   **Service-Centric Dashboard:** Designing the initial dashboard to focus on key metrics for services critical to the AI application's functionality (Cloud Run, Firestore, Vertex AI).
*   **Proactive Alerting Strategy:** Defining a list of recommended alert policies tailored to the common failure modes and performance characteristics of an AI-driven application, including considerations for LLM behavior and data pipeline health.
*   **Security and Compliance Focus:** The logging setup supports auditability requirements for HIPAA. The ability to monitor for security-relevant events (e.g., unauthorized access attempts if logged) is crucial.
