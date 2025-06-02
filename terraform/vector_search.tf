# ------------------------------------------------------------------------------
# Vertex AI Vector Search (formerly Matching Engine) for RAG System
# ------------------------------------------------------------------------------

# GCS Bucket to store RAG pipeline outputs (embeddings JSONL, id-to-chunk map)
resource "google_storage_bucket" "noah_mvp_rag_data_bucket" {
  project                     = google_project.noah_mvp_project.project_id
  name                        = "bkt-noah-mvp-rag-data-${google_project.noah_mvp_project.project_id}" # Must be globally unique
  location                    = var.gcp_region # Or multi-region if appropriate
  uniform_bucket_level_access = true
  storage_class               = "STANDARD"

  # Lifecycle rule for potentially large embedding files if they are versioned or rebuilt often
  # For MVP with small static data, this might be less critical immediately
  # lifecycle_rule {
  #   action { type = "Delete" }
  #   condition { num_newer_versions = 3 } # Example: keep last 3 versions
  # }
}

# Output path for embeddings file (JSONL) in GCS, e.g., gs://<bucket_name>/embeddings/
variable "rag_embeddings_gcs_prefix" {
  description = "GCS prefix (folder) within the RAG data bucket to store the embeddings JSONL files."
  type        = string
  default     = "embeddings_input"
}

# Output path for the ID-to-chunk details map JSON file
variable "rag_chunk_map_gcs_object_name" {
  description = "GCS object name for the ID-to-chunk details map JSON file within the RAG data bucket."
  type        = string
  default     = "metadata/id_to_chunk_details_map.json"
}


# Vertex AI Index for Vector Search
# Note: For the initial index creation with BATCH_UPDATE, `contents_delta_uri` should point
# to the GCS directory containing the JSONL file(s) with embeddings.
# This Terraform configuration creates the index resource; the actual data upload via
# `contents_delta_uri` or `update` method happens outside direct Terraform apply,
# typically via a script or gcloud command after the pipeline generates the data.
# Or, if the data is ready at apply time, TF can create it.
# The script generated will create the data for GCS.

resource "google_vertex_ai_index" "noah_mvp_rag_index" {
  project      = google_project.noah_mvp_project.project_id
  region       = var.gcp_region
  display_name = "noah-mvp-rag-index"
  description  = "Vector index for Project Noah MVP RAG system."
  # index_update_method = "BATCH_UPDATE" # For initial population using contents_delta_uri or streaming.
                                       # For an initially empty index created via TF, then populated by script,
                                       # this might be better managed by the script calling update_embeddings.
                                       # If populated at creation:
  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.noah_mvp_rag_data_bucket.name}/${var.rag_embeddings_gcs_prefix}" # Directory for JSONL files
    config {
      dimensions = 768 # Dimension for textembedding-gecko@003
      approximate_neighbors_count = 10 # Default, can be tuned
      distance_measure_type = "DOT_PRODUCT_DISTANCE" # Or COSINE_DISTANCE, EUCLIDEAN_SQUARED
      # For ANN, choose an algorithm. Brute force for small exact results.
      # Sharding can be configured for larger datasets.
      algorithm_config {
        tree_ah_config { # Example: Tree AH algorithm
          leaf_node_embedding_count = 1000 # Number of embeddings per leaf node
        }
        # Or brute_force_config {} for exact search (good for small datasets)
      }
    }
  }
  # labels = { ... }
  # depends_on = [google_storage_bucket.noah_mvp_rag_data_bucket] # Implicit
}

# Vertex AI Index Endpoint to deploy the index
resource "google_vertex_ai_index_endpoint" "noah_mvp_rag_index_endpoint" {
  project      = google_project.noah_mvp_project.project_id
  region       = var.gcp_region
  display_name = "noah-mvp-rag-index-endpoint"
  description  = "Endpoint for the Project Noah MVP RAG vector index."
  # network = google_compute_network.noah_mvp_vpc.id # For private endpoint (more secure)
  public_endpoint_enabled = true                   # For MVP simplicity using public endpoint
                                                   # Ensure appropriate auth for a public endpoint.
                                                   # Cloud Run service account will need permissions.
}

# Deploying the index to the endpoint using a separate resource:
resource "google_vertex_ai_deployed_index" "noah_mvp_rag_index_deployment_on_endpoint" {
  project          = google_project.noah_mvp_project.project_id
  region           = var.gcp_region
  index_endpoint   = google_vertex_ai_index_endpoint.noah_mvp_rag_index_endpoint.id
  index            = google_vertex_ai_index.noah_mvp_rag_index.name # Using the name attribute which is the full resource path for the index
  deployed_index_id = "noah_mvp_rag_deployed_idx_v1" # User-defined ID for this deployment
  display_name     = "Noah MVP RAG Index Deployment v1"

  # Configuration for the deployment, e.g., machine type for serving
  # For many ANN indexes, specific machine types are recommended.
  # For MVP, default automatic_resources (if that's the provider default behavior for the index type) should be fine.
  # Explicitly using automatic_resources for clarity.
  automatic_resources {
     min_replica_count = 1
     max_replica_count = 1 # For MVP, start with 1, can scale later.
  }

  # depends_on = [
  #   google_vertex_ai_index_endpoint.noah_mvp_rag_index_endpoint,
  #   google_vertex_ai_index.noah_mvp_rag_index
  # ] # Terraform should infer these.
}


# --- Outputs for Vector Search ---
output "rag_data_gcs_bucket_name" {
  description = "Name of the GCS bucket for RAG data (embeddings, metadata map)."
  value       = google_storage_bucket.noah_mvp_rag_data_bucket.name
}

output "rag_embeddings_gcs_path_prefix" {
  description = "GCS path prefix for storing embeddings JSONL files."
  value       = "gs://${google_storage_bucket.noah_mvp_rag_data_bucket.name}/${var.rag_embeddings_gcs_prefix}/"
}

output "rag_chunk_map_gcs_full_path" {
  description = "Full GCS path to the ID-to-chunk details map JSON file."
  value       = "gs://${google_storage_bucket.noah_mvp_rag_data_bucket.name}/${var.rag_chunk_map_gcs_object_name}"
}

output "vertex_ai_rag_index_id" {
  description = "Resource ID of the Vertex AI Vector Search Index (full path)."
  value       = google_vertex_ai_index.noah_mvp_rag_index.id
}

output "vertex_ai_rag_index_name_only" {
  description = "The 'name' part of the Vertex AI Index resource (the last segment of the ID, often used in SDKs)."
  value       = google_vertex_ai_index.noah_mvp_rag_index.name
}


output "vertex_ai_rag_index_endpoint_id" {
  description = "Resource ID of the Vertex AI Index Endpoint (full path)."
  value       = google_vertex_ai_index_endpoint.noah_mvp_rag_index_endpoint.id
}

output "vertex_ai_rag_index_endpoint_public_domain_name" {
  description = "Public domain name of the Vertex AI Index Endpoint if public endpoint enabled."
  value       = google_vertex_ai_index_endpoint.noah_mvp_rag_index_endpoint.public_endpoint_domain_name
}

output "vertex_ai_rag_deployed_index_id_on_endpoint" {
  description = "The user-defined ID of the deployed index on the endpoint."
  value       = google_vertex_ai_deployed_index.noah_mvp_rag_index_deployment_on_endpoint.deployed_index_id
}
