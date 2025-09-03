# app/vector_db.py



import chromadb
from chromadb.utils import embedding_functions
import PyPDF2
import io
import os
import json
from typing import List, Dict, Any
import streamlit as st
import logging
from tqdm import tqdm
from google.cloud import storage
from elasticsearch_utils import ElasticsearchManager

# Set up logging for better debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vector_db.log'),
        logging.StreamHandler()
    ]
)

class VectorDBManager:
    """
    Manages the ChromaDB vector database.
    This version initializes by reading source PDFs and metadata from a Google Cloud Storage bucket.
    """
    def __init__(self, es_manager: ElasticsearchManager, gcs_bucket_name: str):
        self.es_manager = es_manager
        self.gcs_bucket_name = gcs_bucket_name
        self.persist_directory = "vector_db"
        
        # NOTE FOR PRODUCTION: In a scalable app, this rebuilding step would be a separate,
        # offline process. For this Streamlit app, rebuilding on startup is acceptable.
        if os.path.exists(self.persist_directory):
            import shutil
            shutil.rmtree(self.persist_directory)
        
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(name="papers", embedding_function=self.embedding_function)

        # Call the new function that reads from Google Cloud Storage
        self._initialize_with_papers_from_gcs()

    def _initialize_with_papers_from_gcs(self):
        """
        Initializes the database by listing, downloading, and processing papers 
        from the configured Google Cloud Storage bucket.
        """
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(self.gcs_bucket_name)
            blobs = list(bucket.list_blobs())
            pdf_blobs = [blob for blob in blobs if blob.name.lower().endswith('.pdf')]
            
            if not pdf_blobs:
                logging.warning(f"No PDF files found in GCS bucket '{self.gcs_bucket_name}'.")
                return

            logging.info(f"Found {len(pdf_blobs)} PDF files in GCS bucket to process.")

            for blob in tqdm(pdf_blobs, desc="Processing papers from GCS"):
                try:
                    filename = blob.name
                    logging.info(f"Processing {filename} from GCS...")
                    
                    pdf_bytes = blob.download_as_bytes()
                    pdf_stream = io.BytesIO(pdf_bytes)
                    pdf_reader = PyPDF2.PdfReader(pdf_stream)
                    content = "".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())

                    if not content.strip():
                        logging.warning(f"No text content extracted from '{filename}'.")

                    # Try both .json and .metadata.json extensions
                    meta_blob_name = filename.rsplit('.', 1)[0] + '.json'
                    meta_blob = bucket.blob(meta_blob_name)
                    
                    # If .json doesn't exist, try .metadata.json
                    if not meta_blob.exists():
                        meta_blob_name = filename.rsplit('.', 1)[0] + '.metadata.json'
                        meta_blob = bucket.blob(meta_blob_name)
                    metadata = {}
                    if meta_blob.exists():
                        meta_content = meta_blob.download_as_string()
                        metadata = json.loads(meta_content)
                        logging.info(f"Loaded metadata for {filename}: {list(metadata.keys())}")
                    else:
                        metadata = {'title': filename.replace('.pdf', '')}
                        logging.warning(f"No metadata JSON found for {filename}")
                    
                    metadata['paper_id'] = filename
                    
                    self.add_paper(paper_id=filename, content=content, metadata=metadata)
                except Exception as e:
                    logging.error(f"Error processing blob {blob.name} from GCS: {str(e)}")
        except Exception as e:
            logging.error(f"Failed to list files from GCS bucket '{self.gcs_bucket_name}': {e}")
            st.error(f"Could not access GCS bucket '{self.gcs_bucket_name}'. Error: {e}")

    def add_paper(self, paper_id: str, content: str, metadata: Dict[str, Any]):
        """
        Adds a paper's content and metadata to ChromaDB (with robust chunking) and Elasticsearch.
        This method is preserved from your original complete file.
        """
        # --- ChromaDB Logic (with original, detailed chunking) ---
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            if current_length + len(paragraph) > 1000: # Max chunk size
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [paragraph]
                current_length = len(paragraph)
            else:
                current_chunk.append(paragraph)
                current_length += len(paragraph)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        if not chunks:
            chunks = [""]
            
        chunk_ids = [f"{paper_id}_chunk_{i}" for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            ids=chunk_ids,
            metadatas=[metadata] * len(chunks)
        )

        # --- Elasticsearch Indexing Logic ---
        logging.info(f"Indexing paper '{paper_id}' in Elasticsearch...")
        self.es_manager.index_paper(paper_id=paper_id, metadata=metadata, content=content)

    def search_by_keywords(self, keywords: List[str], n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Performs a semantic search in ChromaDB.
        This combines the best parts of your original search logic.
        """
        query = " ".join(keywords)
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2,  # Get more results to de-duplicate
                include=["documents", "metadatas", "distances"]
            )
            processed_results = []
            seen_papers = set()
            if results and results.get('ids') and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    metadata = results['metadatas'][0][i]
                    paper_id = metadata['paper_id']
                    if paper_id in seen_papers:
                        continue
                    if len(processed_results) >= n_results:
                        break
                    
                    distance = results['distances'][0][i] if results.get('distances') else 1.0
                    processed_results.append({
                        'paper_id': paper_id,
                        'content': results['documents'][0][i],
                        'metadata': metadata,
                        'score': 1 - distance
                    })
                    seen_papers.add(paper_id)
            return processed_results
        except Exception as e:
            logging.error(f"Error during ChromaDB search: {e}")
            return []

    def get_all_papers(self) -> List[Dict[str, Any]]:
        """
        Retrieves all unique papers from the collection.
        This logic is preserved from your original file.
        """
        results = self.collection.get(include=["metadatas", "documents"])
        papers = {}
        if results and results.get('ids'):
            for i, metadata in enumerate(results['metadatas']):
                paper_id = metadata.get('paper_id')
                if not paper_id: continue
                if paper_id not in papers:
                    papers[paper_id] = {'content': [], 'metadata': metadata}
                papers[paper_id]['content'].append(results['documents'][i])
        
        return [{'paper_id': paper_id, 'content': ' '.join(data['content']), 'metadata': data['metadata']} for paper_id, data in papers.items()]

    def remove_paper(self, paper_id: str):
        """
        Removes a paper from both ChromaDB and Elasticsearch.
        This logic is preserved from your original file.
        """
        # Remove from Elasticsearch
        self.es_manager.delete_paper(paper_id)
        
        # Remove from ChromaDB
        results = self.collection.get(where={"paper_id": paper_id})
        if results and results['ids']:
            self.collection.delete(ids=results['ids'])

    def get_db_status(self) -> dict:
        """Returns a dictionary with the status of the ChromaDB collection."""
        try:
            return {"status": "Active", "collection_name": self.collection.name, "total_documents_chunks": self.collection.count()}
        except Exception as e:
            return {"status": "Error", "message": str(e)}
    
    def update_paper_metadata(self, paper_id: str, new_metadata: Dict[str, Any]):
        """
        Updates the metadata for a specific paper in both ChromaDB and Elasticsearch.
        """
        try:
            # Update in ChromaDB
            results = self.collection.get(where={"paper_id": paper_id})
            if results and results['ids']:
                # Update all chunks for this paper
                for i, chunk_id in enumerate(results['ids']):
                    updated_metadata = new_metadata.copy()
                    updated_metadata['paper_id'] = paper_id
                    self.collection.update(
                        ids=[chunk_id],
                        metadatas=[updated_metadata]
                    )
                logging.info(f"Updated metadata for {paper_id} in ChromaDB")
            
            # Update in Elasticsearch
            self.es_manager.index_paper(paper_id=paper_id, metadata=new_metadata, content="")
            logging.info(f"Updated metadata for {paper_id} in Elasticsearch")
            
        except Exception as e:
            logging.error(f"Error updating metadata for {paper_id}: {e}")
            raise

# The factory function that connects everything together from secrets
@st.cache_resource
def get_vector_db(_es_manager: ElasticsearchManager) -> VectorDBManager:
    """Gets a cached instance of the VectorDBManager, configured to use GCS."""
    gcs_bucket_name = st.secrets["app_config"]["gcs_bucket_name"]
    return VectorDBManager(es_manager=_es_manager, gcs_bucket_name=gcs_bucket_name)









