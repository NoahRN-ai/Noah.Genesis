import os
import json
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any

from google.cloud import storage
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingsPrediction # For type hinting
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader # For PDF document loading

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Source document directory (relative to project root)
# For MVP, documents are local. In production, this could be a GCS path.
SOURCE_DOCS_DIR = Path(os.getenv("SOURCE_DOCS_DIR", "data/rag_source_docs/"))

# GCS Configuration (from environment variables, set these before running)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION", "us-central1") # Vertex AI services are regional
RAG_GCS_BUCKET_NAME = os.getenv("RAG_GCS_BUCKET_NAME") # Output from terraform/vector_search.tf
EMBEDDINGS_GCS_PREFIX = os.getenv("EMBEDDINGS_GCS_PREFIX", "embeddings_input") # Matches terraform var
CHUNK_MAP_GCS_OBJECT_NAME = os.getenv("CHUNK_MAP_GCS_OBJECT_NAME", "metadata/id_to_chunk_details_map.json") # Matches terraform var

# Vertex AI Embedding Model
EMBEDDING_MODEL_NAME = "textembedding-gecko@003" # Output dimension: 768

# Text Chunking Configuration
CHUNK_SIZE = 1000  # Characters
CHUNK_OVERLAP = 150

# --- Helper Functions ---

def load_documents_from_path(path: Path) -> List[Dict[str, Any]]:
    """Loads documents from various file types in a given path."""
    docs_content = []
    logger.info(f"Loading documents from: {path.resolve()}")
    if not path.exists() or not path.is_dir():
        logger.error(f"Source documents directory not found or is not a directory: {path.resolve()}")
        return []

    for file_path in path.iterdir():
        content = ""
        if file_path.is_file():
            try:
                if file_path.suffix == ".pdf":
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        content += page.extract_text() + "\n"
                    logger.info(f"Loaded PDF: {file_path.name}")
                elif file_path.suffix in [".md", ".txt"]:
                    content = file_path.read_text(encoding="utf-8")
                    logger.info(f"Loaded Text/MD: {file_path.name}")
                else:
                    logger.warning(f"Skipping unsupported file type: {file_path.name}")
                    continue

                if content.strip():
                     docs_content.append({"source_document_name": file_path.name, "raw_text": content.strip()})
                else:
                    logger.warning(f"Empty content for file: {file_path.name}")

            except Exception as e:
                logger.error(f"Error loading document {file_path.name}: {e}")
    return docs_content

def chunk_documents(docs: List[Dict[str, Any]], chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
    """Chunks document texts using RecursiveCharacterTextSplitter."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True, # Useful for metadata
    )
    all_chunks = []
    for doc in docs:
        try:
            chunks = text_splitter.create_documents(
                texts=[doc["raw_text"]],
                metadatas=[{"source_document_name": doc["source_document_name"]}]
            )
            for i, chunk_doc in enumerate(chunks):
                all_chunks.append({
                    "id": str(uuid.uuid4()), # Unique ID for each chunk
                    "chunk_text": chunk_doc.page_content,
                    "source_document_name": chunk_doc.metadata["source_document_name"],
                    "chunk_index_in_doc": i, # Relative index within the original document
                    "start_index_in_doc": chunk_doc.metadata.get("start_index", -1)
                })
            logger.info(f"Chunked {doc['source_document_name']} into {len(chunks)} chunks.")
        except Exception as e:
            logger.error(f"Error chunking document {doc['source_document_name']}: {e}")
    return all_chunks

def generate_embeddings(chunks_texts: List[str], model_name: str) -> List[List[float]]:
    """Generates embeddings for a list of text chunks using Vertex AI Embedding API."""
    try:
        model = TextEmbeddingModel.from_pretrained(model_name)
        # The get_embeddings method can take a list of texts (up to batch limits)
        # For large number of chunks, batching may be required.
        # Max 250 input texts per call for some models; textembedding-gecko's limit is often 5.
        # Let's implement simple batching.
        BATCH_SIZE = 5 # As per gecko@003 docs at times
        all_embeddings_list: List[List[float]] = []

        for i in range(0, len(chunks_texts), BATCH_SIZE):
            batch_texts = chunks_texts[i:i + BATCH_SIZE]
            if not batch_texts: continue

            logger.info(f"Generating embeddings for batch {i // BATCH_SIZE + 1} ({len(batch_texts)} texts)...")
            response: List[TextEmbeddingsPrediction] = model.get_embeddings(batch_texts)
            batch_embeddings = [prediction.values for prediction in response]
            all_embeddings_list.extend(batch_embeddings)
            logger.info(f"Generated embeddings for batch {i // BATCH_SIZE + 1}.")

        return all_embeddings_list
    except Exception as e:
        logger.error(f"Error generating embeddings with model {model_name}: {e}")
        raise

def prepare_vector_search_data(chunks_with_ids: List[Dict[str, Any]], embeddings: List[List[float]]) -> List[Dict[str, Any]]:
    """Prepares data in JSONL format for Vertex AI Vector Search batch import."""
    if len(chunks_with_ids) != len(embeddings):
        raise ValueError("Mismatch between number of chunks and embeddings.")

    vector_search_data = []
    for chunk_info, embedding_vector in zip(chunks_with_ids, embeddings):
        vector_search_data.append({
            "id": chunk_info["id"],
            "embedding": embedding_vector,
            "restricts": [ # Example restricts for filtering - customize as needed
                {"namespace": "source_document", "allow_list": [chunk_info["source_document_name"]]},
                {"namespace": "chunk_index", "allow_list": [str(chunk_info["chunk_index_in_doc"])]}
            ]
            # numeric_restricts could be used for e.g., start_index if needed
        })
    return vector_search_data

def upload_to_gcs(bucket_name: str, destination_blob_name: str, data_content: str, content_type: str = "application/json"):
    """Uploads data to a GCS bucket."""
    try:
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(data_content, content_type=content_type)
        logger.info(f"Successfully uploaded data to gs://{bucket_name}/{destination_blob_name}")
    except Exception as e:
        logger.error(f"Failed to upload to GCS gs://{bucket_name}/{destination_blob_name}: {e}")
        raise

# --- Main Pipeline ---
def run_rag_pipeline():
    logger.info("--- Starting RAG Document Processing Pipeline ---")

    if not all([GCP_PROJECT_ID, GCP_REGION, RAG_GCS_BUCKET_NAME]):
        logger.error("Missing critical environment variables: GCP_PROJECT_ID, GCP_REGION, RAG_GCS_BUCKET_NAME.")
        logger.error("Please set these variables. They can be found in Terraform outputs or your project config.")
        return

    # 0. Initialize Vertex AI (if not done globally for the execution environment)
    try:
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
        logger.info(f"Vertex AI initialized for RAG pipeline in project {GCP_PROJECT_ID}, region {GCP_REGION}.")
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI for RAG pipeline: {e}")
        return

    # 1. Document Loading
    logger.info(f"Step 1: Loading documents from '{SOURCE_DOCS_DIR.resolve()}'...")
    raw_documents = load_documents_from_path(SOURCE_DOCS_DIR)
    if not raw_documents:
        logger.error("No documents loaded. Exiting pipeline.")
        return
    logger.info(f"Loaded {len(raw_documents)} documents.")

    # 2. Text Chunking
    logger.info(f"Step 2: Chunking documents (Chunk Size: {CHUNK_SIZE}, Overlap: {CHUNK_OVERLAP})...")
    chunked_data_with_ids = chunk_documents(raw_documents, CHUNK_SIZE, CHUNK_OVERLAP)
    if not chunked_data_with_ids:
        logger.error("No chunks created. Exiting pipeline.")
        return
    logger.info(f"Created {len(chunked_data_with_ids)} chunks in total.")

    # 3. Embedding Generation
    logger.info(f"Step 3: Generating embeddings using Vertex AI model '{EMBEDDING_MODEL_NAME}'...")
    texts_to_embed = [chunk["chunk_text"] for chunk in chunked_data_with_ids]
    try:
        embedding_vectors = generate_embeddings(texts_to_embed, EMBEDDING_MODEL_NAME)
    except Exception:
        logger.error("Failed to generate embeddings. Exiting pipeline.")
        return

    if len(embedding_vectors) != len(chunked_data_with_ids):
        logger.error(f"Mismatch in number of embeddings ({len(embedding_vectors)}) vs chunks ({len(chunked_data_with_ids)}). Exiting.")
        return
    logger.info(f"Successfully generated {len(embedding_vectors)} embeddings.")

    # 4. Prepare data for Vertex AI Vector Search (JSONL for embeddings)
    # and the ID-to-Chunk_Details map (JSON for service layer retrieval)
    logger.info("Step 4: Preparing data for Vertex AI Vector Search and ID-to-Chunk map...")

    # Data for Vector Search embeddings batch import
    vector_search_jsonl_data = prepare_vector_search_data(chunked_data_with_ids, embedding_vectors)

    # Data for the ID-to-Chunk_Details map (for rag_service.py to get text from ID)
    id_to_chunk_details_map = {}
    for chunk_info in chunked_data_with_ids:
        id_to_chunk_details_map[chunk_info["id"]] = {
            "text": chunk_info["chunk_text"],
            "source": chunk_info["source_document_name"],
            "chunk_idx": chunk_info["chunk_index_in_doc"],
            "start_idx": chunk_info["start_index_in_doc"]
            # Add any other metadata you want to retrieve alongside the chunk
        }

    # 5. Upload to GCS
    logger.info(f"Step 5: Uploading generated files to GCS Bucket '{RAG_GCS_BUCKET_NAME}'...")

    # Upload embeddings JSONL file (Vector Search will read from a directory)
    # Typically, Vector Search ingests from a directory of JSONL files.
    # We'll create one file for this MVP. File name can be fixed or timestamped.
    embeddings_jsonl_content = "\n".join([json.dumps(item) for item in vector_search_jsonl_data])
    embeddings_blob_name = f"{EMBEDDINGS_GCS_PREFIX.strip('/')}/embeddings_batch_1.jsonl"
    upload_to_gcs(RAG_GCS_BUCKET_NAME, embeddings_blob_name, embeddings_jsonl_content, "application/jsonl")

    # Upload ID-to-Chunk_Details map
    chunk_map_json_content = json.dumps(id_to_chunk_details_map, indent=2)
    upload_to_gcs(RAG_GCS_BUCKET_NAME, CHUNK_MAP_GCS_OBJECT_NAME, chunk_map_json_content, "application/json")

    logger.info("--- RAG Document Processing Pipeline Finished Successfully ---")
    logger.info(f"Embeddings data uploaded to: gs://{RAG_GCS_BUCKET_NAME}/{embeddings_blob_name}")
    logger.info(f"Chunk metadata map uploaded to: gs://{RAG_GCS_BUCKET_NAME}/{CHUNK_MAP_GCS_OBJECT_NAME}")
    logger.info("Next step: Ensure your Vertex AI Vector Search Index is configured to read from the embeddings GCS path if using BATCH_UPDATE at index creation, or use the gcloud CLI or SDK to update/rebuild the index with this data.")

if __name__ == "__main__":
    # This allows running the script directly.
    # Ensure environment variables are set before running:
    # export GCP_PROJECT_ID="your-gcp-project-id"
    # export GCP_REGION="your-gcp-region" # e.g., us-central1
    # export RAG_GCS_BUCKET_NAME="your-rag-data-bucket-name" # From TF output
    # (Optional) export SOURCE_DOCS_DIR="path/to/your/docs"
    # (Optional) export EMBEDDINGS_GCS_PREFIX="embeddings_input"
    # (Optional) export CHUNK_MAP_GCS_OBJECT_NAME="metadata/id_to_chunk_details_map.json"

    # Example local document structure for testing:
    # project_root/
    #  data/
    #    rag_source_docs/
    #      doc1.pdf
    #      notes.txt
    #  scripts/
    #    rag_pipeline/
    #      01_process_and_embed_docs.py
    # To run from project_root: python scripts/rag_pipeline/01_process_and_embed_docs.py

    # Create dummy source_docs_dir if it doesn't exist for a dry run structure.
    if not SOURCE_DOCS_DIR.exists():
        SOURCE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created dummy source documents directory: {SOURCE_DOCS_DIR}")
        # Create a dummy file for testing if desired
        # (SOURCE_DOCS_DIR / "sample_notes.txt").write_text("This is a sample document for Project Noah RAG.")

    run_rag_pipeline()
