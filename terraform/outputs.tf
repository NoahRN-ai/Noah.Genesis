output "project_id" {
  description = "The ID of the created Google Cloud Project for Noah MVP."
  value       = google_project.noah_mvp_project.project_id
}

output "project_number" {
  description = "The number of the created Google Cloud Project for Noah MVP."
  value       = google_project.noah_mvp_project.number
}

output "sa_cloudrun_agent_email" {
  description = "Email of the AI Agent Cloud Run service account."
  value       = google_service_account.sa_cloudrun_agent.email
}

output "sa_cloudrun_webapp_email" {
  description = "Email of the WebApp Cloud Run service account."
  value       = google_service_account.sa_cloudrun_webapp.email
}

output "sa_rag_pipeline_email" {
  description = "Email of the RAG Pipeline service account."
  value       = google_service_account.sa_rag_pipeline.email
}
