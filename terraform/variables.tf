variable "gcp_project_id" {
  description = "The desired unique ID for the new Google Cloud Project. Must be unique globally."
  type        = string
}

variable "gcp_project_name" {
  description = "The display name for the new Google Cloud Project."
  type        = string
}

variable "gcp_org_id" {
  description = "The Google Cloud Organization ID that the project will belong to."
  type        = string
}

variable "gcp_billing_account" {
  description = "The Google Cloud Billing Account ID to associate with the project."
  type        = string
}

variable "gcp_region" {
  description = "The default GCP region for resources."
  type        = string
  default     = "us-central1" # As per TA_Noah_MVP_v1.1 recommendations generally lean to US regions for initial setup
}

variable "aem_developer_group_email" {
  description = "Optional: The email address of the Google Group for AEM developers who need project access."
  type        = string
  default     = null
}

variable "aem_developer_user_email" {
  description = "Optional: The email address of a primary AEM developer user who needs project access."
  type        = string
  default     = null
}
