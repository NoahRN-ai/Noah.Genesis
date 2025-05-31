# ------------------------------------------------------------------------------
# Cloud Storage Bucket for Log Archival
# ------------------------------------------------------------------------------
variable "log_archive_bucket_name_suffix" {
  description = "Suffix for the log archive bucket name to ensure uniqueness if needed."
  type        = string
  default     = "" # Can be set to a random ID or specific suffix by user
}

variable "log_archive_retention_period_days" {
  description = "Number of days to retain logs in the archive bucket before deletion. HIPAA considerations may require long retention (e.g., 2190 days for 6 years)."
  type        = number
  default     = 2190 # 6 years
}

resource "google_storage_bucket" "noah_mvp_log_archive_bucket" {
  project      = google_project.noah_mvp_project.project_id
  name         = "bkt-noah-mvp-logs-archive-${google_project.noah_mvp_project.project_id}${var.log_archive_bucket_name_suffix}"
  location     = var.gcp_region # Or a multi-region like "US" for higher availability of bucket metadata
  storage_class = "STANDARD"    # Start with STANDARD, then transition using lifecycle rules
  uniform_bucket_level_access = true

  lifecycle_rule {
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      age = 30 # Days to transition to Nearline
    }
  }

  lifecycle_rule {
    action {
      type = "SetStorageClass"
      storage_class = "COLDLINE"
    }
    condition {
      age = 90 # Days to transition to Coldline
    }
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = var.log_archive_retention_period_days # Matched to retention requirements
    }
  }
  # Versioning can be enabled for added protection against accidental deletion/overwrite
  # versioning {
  #   enabled = true
  # }
}

# ------------------------------------------------------------------------------
# BigQuery Dataset for Log Analysis
# ------------------------------------------------------------------------------
variable "bigquery_log_dataset_id" {
  description = "ID for the BigQuery dataset to store logs for analysis."
  type        = string
  default     = "noah_mvp_logs_analysis"
}

variable "bigquery_log_dataset_location" {
  description = "Location for the BigQuery dataset (e.g., US, EU, or a specific region)."
  type        = string
  default     = "US" # Choose based on data residency requirements
}

resource "google_bigquery_dataset" "noah_mvp_logs_analysis_dataset" {
  project    = google_project.noah_mvp_project.project_id
  dataset_id = var.bigquery_log_dataset_id
  location   = var.bigquery_log_dataset_location
  description = "Dataset for storing Project Noah MVP logs for analysis."
  # Default table expiration can be set here if desired
  # default_table_expiration_ms = 365 * 24 * 60 * 60 * 1000 # 1 year example
}

# ------------------------------------------------------------------------------
# Logging Sinks
# ------------------------------------------------------------------------------

# Sink to Cloud Storage for archival
resource "google_logging_project_sink" "noah_mvp_gcs_log_sink" {
  project              = google_project.noah_mvp_project.project_id
  name                 = "noah-mvp-gcs-archive-sink"
  destination          = "storage.googleapis.com/${google_storage_bucket.noah_mvp_log_archive_bucket.name}"
  filter               = "severity >= DEFAULT" # Captures most logs, can be adjusted
  unique_writer_identity = true
}

# Grant permission to the GCS sink's writer identity to write to the bucket
resource "google_storage_bucket_iam_member" "gcs_log_sink_writer_permissions" {
  bucket = google_storage_bucket.noah_mvp_log_archive_bucket.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.noah_mvp_gcs_log_sink.writer_identity
}

# Sink to BigQuery for analysis
resource "google_logging_project_sink" "noah_mvp_bq_log_sink" {
  project              = google_project.noah_mvp_project.project_id
  name                 = "noah-mvp-bq-analysis-sink"
  destination          = "bigquery.googleapis.com/projects/${google_project.noah_mvp_project.project_id}/datasets/${google_bigquery_dataset.noah_mvp_logs_analysis_dataset.dataset_id}"
  filter               = "severity >= INFO" # Capture INFO and above for analysis, can be adjusted
  unique_writer_identity = true
  # BigQuery options can be set here, e.g., use_partitioned_tables (default is true)
}

# Grant permission to the BigQuery sink's writer identity to write to the dataset
resource "google_bigquery_dataset_iam_member" "bq_log_sink_writer_permissions" {
  project    = google_bigquery_dataset.noah_mvp_logs_analysis_dataset.project
  dataset_id = google_bigquery_dataset.noah_mvp_logs_analysis_dataset.dataset_id
  role       = "roles/bigquery.dataEditor" # Allows sink to write data and create tables
  member     = google_logging_project_sink.noah_mvp_bq_log_sink.writer_identity
}

# ------------------------------------------------------------------------------
# Basic Cloud Monitoring Dashboard for Core MVP Service Health
# Dashboard JSON can be extensive. This is a minimal example.
# It is often easier to create dashboards via UI and export JSON, then paste here.
# Replace 'YOUR_PROJECT_ID_PLACEHOLDER' with google_project.noah_mvp_project.project_id
# Replace 'YOUR_AGENT_SERVICE_NAME' and 'YOUR_WEBAPP_SERVICE_NAME' with actual Cloud Run service names after deployment.
# Replace 'YOUR_LLM_ENDPOINT_ID' with actual Vertex AI Endpoint ID after deployment.
# Using dynamic references via ${} for these IDs inside the JSON string.
# ------------------------------------------------------------------------------
resource "google_monitoring_dashboard" "noah_mvp_overview_dashboard" {
  project        = google_project.noah_mvp_project.project_id
  dashboard_json = <<-EOT
  {
    "displayName": "Noah MVP - Core Services Overview",
    "gridLayout": {
      "columns": "2",
      "widgets": [
        {
          "title": "Cloud Run - AI Agent: Request Count (Sum)",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"noah-mvp-agent-service\"", // Assume service name
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_SUM",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                },
                "unitOverride": "1"
              },
              "plotType": "LINE"
            }],
            "timeshiftDuration": "0s",
            "yAxis": {"label": "count", "scale": "LINEAR"}
          }
        },
        {
          "title": "Cloud Run - AI Agent: 5XX Error Count (Sum)",
           "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"noah-mvp-agent-service\" metric.label.response_code_class=\"5xx\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_SUM",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE"
            }],
            "timeshiftDuration": "0s",
            "yAxis": {"label": "count", "scale": "LINEAR"}
          }
        },
        {
          "title": "Firestore: Document Read Operations (Sum)",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"firestore.googleapis.com/document/read_count\" resource.type=\"firestore_database\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_SUM",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE"
            }],
            "timeshiftDuration": "0s",
            "yAxis": {"label": "count", "scale": "LINEAR"}
          }
        },
        {
          "title": "Vertex AI Endpoints: Prediction Request Count (Project Total)",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"aiplatform.googleapis.com/prediction/request_count\" resource.type=\"aiplatform.googleapis.com/Endpoint\"", // Or "aiplatform.googleapis.com/OnlinePrediction"
                  "aggregation": {
                     "perSeriesAligner": "ALIGN_SUM",
                     "crossSeriesReducer": "REDUCE_SUM",
                     "alignmentPeriod": "60s"
                  }
                }
              },
              "plotType": "LINE"
            }],
            "timeshiftDuration": "0s",
            "yAxis": {"label": "count", "scale": "LINEAR"}
          }
        }
      ]
    }
  }
  EOT
}


# ------------------------------------------------------------------------------
# Example Alert Policy (Cloud Run 5XX Errors)
# Define other critical alerts as needed.
# ------------------------------------------------------------------------------
resource "google_monitoring_alert_policy" "cloud_run_agent_5xx_error_alert" {
  project      = google_project.noah_mvp_project.project_id
  display_name = "Cloud Run AI Agent - High 5XX Error Rate"
  combiner     = "OR"
  conditions {
    display_name = "Cloud Run AI Agent Service - 5XX responses"
    condition_threshold {
      filter     = "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"noah-mvp-agent-service\" metric.label.response_code_class=\"5xx\"" // Placeholder, update service_name
      comparison = "COMPARISON_GT"
      threshold_value = 5 # Alert if more than 5 errors...
      duration        = "300s" # ...in a 5-minute window
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE" // or ALIGN_SUM depending on what you want to threshold on
      }
      trigger {
        count = 1 # Alert if the condition is met once
      }
    }
  }
  # Notification channels need to be configured separately (e.g., email, PagerDuty)
  # notification_channels = [google_monitoring_notification_channel.email.id]
  # user_labels = {
  #   "severity" = "critical",
  #   "team" = "noah-devops"
  # }
  # enabled = true (defaults to true)
}
