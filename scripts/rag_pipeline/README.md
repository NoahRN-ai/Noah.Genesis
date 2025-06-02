# RAG Document Processing and Embedding Pipeline (`scripts/rag_pipeline/`)

This directory contains scripts for processing source documents, generating embeddings, and preparing data for ingestion into the Vertex AI Vector Search index used by Project Noah MVP's Retrieval Augmented Generation (RAG) system.

## Pipeline Overview (`01_process_and_embed_docs.py`)

The main script `01_process_and_embed_docs.py` performs the following steps:

1.  **Document Loading:**
    *   Loads text content from files (`.pdf`, `.txt`, `.md`) located in a specified source directory (default: `data/rag_source_docs/`).
    *   PDFs are processed using `pypdf`.

2.  **Text Chunking:**
    *   Splits the loaded document texts into smaller, manageable chunks using LangChain's `RecursiveCharacterTextSplitter`.
    *   Chunk size and overlap are configurable (defaults: 1000 chars size, 150 chars overlap).
    *   Each chunk is assigned a unique UUID. Metadata like `source_document_name`, `chunk_index_in_doc`, and `start_index_in_doc` are associated with each chunk.

3.  **Embedding Generation:**
    *   Generates vector embeddings for each text chunk using Google's Vertex AI Text Embedding API.
    *   **Model:** `textembedding-gecko@003` (Output dimension: 768).
    *   Handles batching of texts for the embedding API calls.

4.  **Data Preparation & Upload to GCS:**
    *   **Embeddings for Vertex AI Vector Search:**
        *   Formats the chunk IDs and their corresponding embeddings into a JSONL (JSON Lines) file. Each line is a JSON object: `{"id": "chunk_uuid", "embedding": [0.1, ..., 0.2], "restricts": [...]}`.
        *   The `restricts` field can be used for pre-filtering in Vector Search (e.g., by source document).
        *   This JSONL file is uploaded to a specified GCS bucket and prefix (e.g., `gs://<RAG_BUCKET_NAME>/<EMBEDDINGS_PREFIX>/embeddings_batch_1.jsonl`). The Vertex AI Vector Search Index will be configured to read from this GCS location for batch updates/creation.
    *   **ID-to-Chunk Details Map:**
        *   Creates a JSON file mapping each chunk's UUID to its actual `chunk_text`, `source_document_name`, and other relevant metadata.
        *   This map is uploaded to a specified GCS bucket (e.g., `gs://<RAG_BUCKET_NAME>/<CHUNK_MAP_OBJECT_NAME>`).
        *   The `rag_service.py` will download and use this map to retrieve the actual text and source information for chunks whose IDs are returned by Vector Search. This is crucial for providing context to the LLM and adhering to the `ALETHIA_FIDELITY_CONSTRAINT` (showing sources).

## Prerequisites

1.  **Python Environment:** Poetry environment set up as per `DEVELOPMENT.md`. Ensure `langchain-text-splitters` and `pypdf` are installed (`poetry add langchain-text-splitters pypdf`).
2.  **Source Documents:** Place your curated knowledge documents (PDFs, TXT, MD files) into the `data/rag_source_docs/` directory (or configure `SOURCE_DOCS_DIR` environment variable).
3.  **GCP Authentication:** Ensure you are authenticated with GCP and have permissions to use Vertex AI Embedding API and write to GCS:
    ```bash
    gcloud auth application-default login
    ```
4.  **Environment Variables:** Set the following environment variables before running the script:
    *   `GCP_PROJECT_ID`: Your Google Cloud Project ID.
    *   `GCP_REGION`: The GCP region for Vertex AI services (e.g., `us-central1`).
    *   `RAG_GCS_BUCKET_NAME`: Name of the GCS bucket (created by `terraform/vector_search.tf`) where pipeline outputs will be stored.
    *   `EMBEDDINGS_GCS_PREFIX` (Optional): GCS prefix for embeddings JSONL files (default: `embeddings_input`).
    *   `CHUNK_MAP_GCS_OBJECT_NAME` (Optional): GCS object name for the ID-to-chunk map (default: `metadata/id_to_chunk_details_map.json`).
    *   `SOURCE_DOCS_DIR` (Optional): Path to your source documents directory (default: `data/rag_source_docs/`).

    Example:
    ```bash
    export GCP_PROJECT_ID="your-noah-mvp-project-id"
    export GCP_REGION="us-central1"
    export RAG_GCS_BUCKET_NAME="bkt-noah-mvp-rag-data-your-project-id"
    # (Get actual bucket name from 'terraform output rag_data_gcs_bucket_name')
    ```

## How to Run the Pipeline

Navigate to the project root directory (`Noah.Genesis/`) and run:

```bash
poetry run python scripts/rag_pipeline/01_process_and_embed_docs.py
```

The script will log its progress and indicate the GCS locations of the uploaded files upon completion.

## Output

*   An `embeddings_batch_1.jsonl` file (or similar) under the `EMBEDDINGS_GCS_PREFIX` in your `RAG_GCS_BUCKET_NAME`. This file is used by Vertex AI Vector Search to build/update its index.
*   An `id_to_chunk_details_map.json` file (or as specified by `CHUNK_MAP_GCS_OBJECT_NAME`) in your `RAG_GCS_BUCKET_NAME`. This file is used by `backend/app/services/rag_service.py`.

## After Running the Pipeline

*   **Vertex AI Vector Search Index Update:** After the `embeddings_batch_1.jsonl` (and potentially other batch files) are on GCS:
    *   If your Terraform `google_vertex_ai_index` resource was configured with `index_update_method = "BATCH_UPDATE"` and its `metadata.contents_delta_uri` points to the GCS directory where these files are, creating or updating the index resource via Terraform *might* trigger an update if it detects changes.
    *   More commonly or for subsequent updates, you would use the Vertex AI SDK or `gcloud` to explicitly update the index with the new data from GCS. Example:
        ```bash
        # (Using gcloud CLI as an example - SDK is also an option)
        # Get your index ID from 'terraform output vertex_ai_rag_index_name_only'
        gcloud ai indexes update YOUR_INDEX_ID \
          --metadata-file=path/to/your/index_metadata_update_config.yaml \
          --project=YOUR_PROJECT_ID \
          --region=YOUR_REGION
        ```
        Where `index_metadata_update_config.yaml` would specify the new `contentsDeltaUri`.
    *   Alternatively, the `Index.update_embeddings()` method in the SDK can be used if you're managing data incrementally.
*   For the initial MVP setup with `BATCH_UPDATE` via `contents_delta_uri` in Terraform, ensure the GCS path contains the embedding files *before* `terraform apply` creates/updates the `google_vertex_ai_index` resource for the index data to be picked up at creation time. If Terraform only creates an empty index shell, then a manual update/rebuild step is necessary after the pipeline script uploads data.
The Terraform in `vector_search.tf` aims to set the `contents_delta_uri` during index creation. So, the pipeline should be run *before* or concurrently with `terraform apply` if that's the trigger for the index build from GCS.
