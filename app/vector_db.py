# import chromadb
# from chromadb.utils import embedding_functions
# import PyPDF2
# import io
# import os
# from typing import List, Dict, Any
# import streamlit as st
# import logging
# from tqdm import tqdm

# # Set up logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('vector_db.log'),
#         logging.StreamHandler()
#     ]
# )

# # Define the papers directory
# PAPERS_DIRECTORY = "/Users/mahirselek/Desktop/DSPhD/Polo-GGB/all-papers/pdf-metadata"

# class VectorDBManager:
#     def __init__(self):
#         """
#         Initialize the vector database manager.
#         Automatically processes and adds papers from the predefined directory.
#         """
#         self.persist_directory = "vector_db"
        
#         # Always remove existing database to ensure fresh initialization
#         if os.path.exists(self.persist_directory):
#             logging.info("Removing existing vector database to ensure fresh initialization...")
#             import shutil
#             shutil.rmtree(self.persist_directory)
#             logging.info("Existing database removed.")
        
#         self.client = chromadb.PersistentClient(path=self.persist_directory)
        
#         # Use sentence-transformers for embeddings
#         self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
#             model_name="all-MiniLM-L6-v2"
#         )
        
#         # Create or get collection
#         self.collection = self.client.get_or_create_collection(
#             name="papers",
#             embedding_function=self.embedding_function
#         )

#         # Always process papers from the predefined directory
#         self._initialize_with_papers()

#     def _initialize_with_papers(self):
#         """
#         Initialize the database with papers from the predefined directory.
#         """
#         if not os.path.exists(PAPERS_DIRECTORY):
#             logging.error(f"Directory not found: {PAPERS_DIRECTORY}")
#             return

#         # Get list of PDF files (including subdirectories)
#         pdf_files = []
#         for root, _, files in os.walk(PAPERS_DIRECTORY):
#             for file in files:
#                 if file.endswith('.pdf'):
#                     pdf_files.append(os.path.join(root, file))

#         if not pdf_files:
#             logging.warning(f"No PDF files found in {PAPERS_DIRECTORY}")
#             return

#         logging.info(f"Found {len(pdf_files)} PDF files to process")

#         # Process each PDF file
#         for file_path in tqdm(pdf_files, desc="Processing papers"):
#             try:
#                 filename = os.path.basename(file_path)
#                 logging.info(f"Processing {filename}...")

#                 # Read PDF content
#                 with open(file_path, 'rb') as file:
#                     pdf_reader = PyPDF2.PdfReader(file)
#                     content = ""
#                     for page in pdf_reader.pages:
#                         content += page.extract_text()

#                     if not content.strip():
#                         logging.warning(f"No text content extracted from {filename}")
#                         continue

#                     # Add paper to vector database
#                     self.add_paper(
#                         paper_id=filename,
#                         content=content,
#                         metadata={
#                             'paper_id': filename,
#                             'title': filename.replace('.pdf', ''),
#                             'file_path': file_path,
#                             'source': 'pre_loaded'
#                         }
#                     )

#                 logging.info(f"Successfully added {filename} to the database")

#             except Exception as e:
#                 logging.error(f"Error processing {file_path}: {str(e)}")

#         # Log summary
#         papers = self.get_all_papers()
#         logging.info(f"Database initialization complete. Total papers in database: {len(papers)}")
#         logging.info("\nPapers in database:")
#         for paper in papers:
#             logging.info(f"- {paper['metadata']['title']}")

#     def add_paper(self, paper_id: str, content: str, metadata: Dict[str, Any]):
#         """
#         Add a paper to the vector database with improved chunking.
#         Allows empty content for metadata-only papers.
#         """
#         # If content is empty or None, add a placeholder chunk
#         if not content or not content.strip():
#             self.collection.add(
#                 documents=[""],
#                 ids=[f"{paper_id}_chunk_0"],
#                 metadatas=[metadata]
#             )
#             return
#         # Improved chunking strategy
#         # Split by paragraphs but ensure chunks are meaningful
#         paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
#         chunks = []
#         current_chunk = []
#         current_length = 0
        
#         for paragraph in paragraphs:
#             # If adding this paragraph would make the chunk too long, save current chunk
#             if current_length + len(paragraph) > 1000:  # Maximum chunk size
#                 if current_chunk:
#                     chunks.append(' '.join(current_chunk))
#                 current_chunk = [paragraph]
#                 current_length = len(paragraph)
#             else:
#                 current_chunk.append(paragraph)
#                 current_length += len(paragraph)
        
#         # Add the last chunk if it exists
#         if current_chunk:
#             chunks.append(' '.join(current_chunk))
        
#         # Create chunk IDs
#         chunk_ids = [f"{paper_id}_chunk_{i}" for i in range(len(chunks))]
        
#         # Add chunks to collection
#         self.collection.add(
#             documents=chunks,
#             ids=chunk_ids,
#             metadatas=[metadata for _ in chunks]
#         )

#     def add_metadata_only_paper(self, paper_id: str, metadata: Dict[str, Any]):
#         """
#         Add a metadata-only paper (no content) to the vector database.
#         """
#         self.add_paper(paper_id=paper_id, content="", metadata=metadata)

#     def bulk_import_metadata_only(self, metadata_dir: str):
#         """
#         Bulk import all metadata-only papers from a directory containing JSON files.
#         """
#         import json
#         for fname in os.listdir(metadata_dir):
#             if fname.endswith('.json'):
#                 fpath = os.path.join(metadata_dir, fname)
#                 with open(fpath, 'r') as f:
#                     metadata = json.load(f)
#                 paper_id = metadata.get('pdf_filename', fname.replace('.json', '.pdf'))
#                 self.add_metadata_only_paper(paper_id, metadata)

#     def search_by_keywords(self, keywords: List[str], n_results: int = 5) -> List[Dict[str, Any]]:
#         """
#         Search papers using keywords with improved relevance scoring and debug logging.
#         Includes metadata-only papers (no content) if their metadata matches keywords.
#         """
#         logging.info(f"Starting keyword search with keywords: {keywords}")
        
#         # First, verify we have papers in the database
#         all_papers = self.get_all_papers()
#         logging.info(f"Total papers in database: {len(all_papers)}")
#         if not all_papers:
#             logging.error("No papers found in database!")
#             return []
            
#         # Log paper titles for debugging
#         logging.info("Papers in database:")
#         for paper in all_papers:
#             logging.info(f"- {paper['metadata']['title']}")
        
#         # Create a more sophisticated query that emphasizes the importance of each keyword
#         query_parts = []
#         for keyword in keywords:
#             # Add each keyword with a weight to emphasize exact matches
#             query_parts.append(f'"{keyword}"')  # Exact phrase matching
#             query_parts.append(keyword)  # Individual word matching
        
#         # Combine query parts with OR operator to find papers matching any keyword
#         query = " OR ".join(query_parts)
#         logging.info(f"Generated search query: {query}")
        
#         try:
#             # Search the collection with increased n_results to allow for better filtering
#             results = self.collection.query(
#                 query_texts=[query],
#                 n_results=n_results * 2,  # Get more results for better filtering
#                 include=["documents", "metadatas", "distances"]
#             )
            
#             logging.info(f"Raw search results count: {len(results['documents'][0]) if results['documents'] else 0}")
            
#             # Process and score results
#             processed_results = []
#             seen_papers = set()  # Track unique papers
            
#             for i in range(len(results['documents'][0])):
#                 content = results['documents'][0][i]
#                 metadata = results['metadatas'][0][i]
#                 distance = results['distances'][0][i]
                
#                 # Skip if we've already processed this paper
#                 paper_id = metadata['paper_id']
#                 if paper_id in seen_papers:
#                     continue
                
#                 # Calculate keyword presence score
#                 keyword_presence = sum(1 for keyword in keywords if keyword.lower() in content.lower())
#                 keyword_score = keyword_presence / len(keywords)  # Normalize by number of keywords
                
#                 # Calculate final similarity score
#                 distance_score = 1 - distance  # Convert distance to similarity
#                 final_score = (distance_score * 0.7) + (keyword_score * 0.3)  # Weighted combination
                
#                 logging.info(f"Paper: {metadata['title']}")
#                 logging.info(f"- Distance score: {distance_score:.3f}")
#                 logging.info(f"- Keyword score: {keyword_score:.3f}")
#                 logging.info(f"- Final score: {final_score:.3f}")
#                 logging.info(f"- Keyword matches: {keyword_presence}")
                
#                 # Only include results with positive relevance
#                 if final_score > 0:
#                     processed_results.append({
#                         'content': content,
#                         'metadata': metadata,
#                         'similarity_score': final_score,
#                         'keyword_matches': keyword_presence
#                     })
#                     seen_papers.add(paper_id)
            
#             # --- Add metadata-only papers not already included ---
#             for paper in all_papers:
#                 if paper['paper_id'] in seen_papers:
#                     continue
#                 content = paper['content']
#                 metadata = paper['metadata']
#                 # If content is empty, check if metadata matches keywords
#                 if not content.strip():
#                     keyword_presence = sum(
#                         1 for keyword in keywords if any(
#                             keyword.lower() in str(metadata.get(field, '')).lower()
#                             for field in ['title', 'abstract', 'journal', 'authors']
#                         )
#                     )
#                     if keyword_presence > 0:
#                         processed_results.append({
#                             'content': '',
#                             'metadata': metadata,
#                             'similarity_score': 0.2 + 0.8 * (keyword_presence / len(keywords)),
#                             'keyword_matches': keyword_presence
#                         })
#                         seen_papers.add(paper['paper_id'])
#             # Sort by similarity score and take top n_results
#             processed_results.sort(key=lambda x: x['similarity_score'], reverse=True)
#             final_results = processed_results[:n_results]
            
#             logging.info(f"Final processed results count: {len(final_results)}")
#             if not final_results:
#                 logging.warning("No results passed the relevance threshold!")
            
#             return final_results
            
#         except Exception as e:
#             logging.error(f"Error during search: {str(e)}")
#             return []

#     def get_all_papers(self) -> List[Dict[str, Any]]:
#         """
#         Get all papers from the database.
        
#         Returns:
#             List[Dict[str, Any]]: List of all papers with their metadata
#         """
#         results = self.collection.get()
        
#         # Group chunks by paper ID
#         papers = {}
#         for i, metadata in enumerate(results['metadatas']):
#             paper_id = metadata['paper_id']
#             if paper_id not in papers:
#                 papers[paper_id] = {
#                     'content': [],
#                     'metadata': metadata
#                 }
#             papers[paper_id]['content'].append(results['documents'][i])
        
#         # Convert to list and join chunks
#         return [
#             {
#                 'paper_id': paper_id,
#                 'content': ' '.join(data['content']),
#                 'metadata': data['metadata']
#             }
#             for paper_id, data in papers.items()
#         ]

#     def remove_paper(self, paper_id: str):
#         """
#         Remove a paper and its chunks from the database.
        
#         Args:
#             paper_id (str): ID of the paper to remove
#         """
#         try:
#             # Get all chunks for this paper
#             results = self.collection.get(
#                 where={"paper_id": paper_id}
#             )
            
#             if results and results['ids']:
#                 # Delete all chunks
#                 self.collection.delete(
#                     ids=results['ids']
#                 )
            
#             # Also delete the physical file if it exists
#             file_path = os.path.join(
#                 os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
#                 'papers',
#                 paper_id
#             )
#             if os.path.exists(file_path):
#                 os.remove(file_path)
                
#         except Exception as e:
#             raise Exception(f"Error removing paper {paper_id}: {str(e)}")

# # Create a function to get the vector database instance
# def get_vector_db() -> VectorDBManager:
#     """
#     Get or create a vector database instance.
#     The database will be automatically initialized with papers from the predefined directory.
    
#     Returns:
#         VectorDBManager: Vector database manager instance
#     """
#     return VectorDBManager() 


































import chromadb
from chromadb.utils import embedding_functions
import PyPDF2
import io
import os
from typing import List, Dict, Any
import streamlit as st
import logging
from tqdm import tqdm
# ### MODIFICATION START ###
# Import the new Elasticsearch manager
from elasticsearch_utils import ElasticsearchManager
# ### MODIFICATION END ###

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vector_db.log'),
        logging.StreamHandler()
    ]
)

# Define the papers directory
PAPERS_DIRECTORY = "/Users/mahirselek/Desktop/DSPhD/Polo-GGB/all-papers/pdf-metadata"

class VectorDBManager:
    # ### MODIFICATION START ###
    # Add es_manager to the constructor
    def __init__(self, es_manager: ElasticsearchManager):
    # ### MODIFICATION END ###
        """
        Initialize the vector database manager.
        Automatically processes and adds papers from the predefined directory.
        """
        # ### MODIFICATION START ###
        self.es_manager = es_manager
        # ### MODIFICATION END ###

        self.persist_directory = "vector_db"
        
        if os.path.exists(self.persist_directory):
            logging.info("Removing existing vector database to ensure fresh initialization...")
            import shutil
            shutil.rmtree(self.persist_directory)
            logging.info("Existing database removed.")
        
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="papers",
            embedding_function=self.embedding_function
        )

        self._initialize_with_papers()

    def _initialize_with_papers(self):
        """
        Initialize the database with papers from the predefined directory.
        """
        # This part remains largely the same, but the call to add_paper will now also index to ES.
        if not os.path.exists(PAPERS_DIRECTORY):
            logging.error(f"Directory not found: {PAPERS_DIRECTORY}")
            return
        
        pdf_files = []
        for root, _, files in os.walk(PAPERS_DIRECTORY):
            for file in files:
                if file.endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))

        if not pdf_files:
            logging.warning(f"No PDF files found in {PAPERS_DIRECTORY}")
            return

        logging.info(f"Found {len(pdf_files)} PDF files to process for ChromaDB and Elasticsearch")

        for file_path in tqdm(pdf_files, desc="Processing papers"):
            try:
                filename = os.path.basename(file_path)
                logging.info(f"Processing {filename}...")

                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    content = "".join(page.extract_text() for page in pdf_reader.pages)

                    if not content.strip():
                        logging.warning(f"No text content extracted from {filename}")
                        continue
                    
                    # Assume metadata file exists with same name but .json extension
                    meta_path = file_path.replace('.pdf', '.json')
                    metadata = {}
                    if os.path.exists(meta_path):
                        import json
                        with open(meta_path, 'r') as mf:
                            metadata = json.load(mf)
                    
                    # Fallback metadata if JSON not found
                    if not metadata:
                        metadata = {
                            'title': filename.replace('.pdf', ''),
                            'source': 'pre_loaded_no_meta'
                        }
                    
                    metadata['paper_id'] = filename # Ensure paper_id is consistent
                    
                    self.add_paper(
                        paper_id=filename,
                        content=content,
                        metadata=metadata
                    )

            except Exception as e:
                logging.error(f"Error processing {file_path}: {str(e)}")

    def add_paper(self, paper_id: str, content: str, metadata: Dict[str, Any]):
        """
        Add a paper to ChromaDB and also index it in Elasticsearch.
        """
        # --- ChromaDB Logic (largely unchanged) ---
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            if current_length + len(paragraph) > 1000:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [paragraph]
                current_length = len(paragraph)
            else:
                current_chunk.append(paragraph)
                current_length += len(paragraph)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # If content is empty, use a placeholder
        if not chunks:
            chunks = [""]
            
        chunk_ids = [f"{paper_id}_chunk_{i}" for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            ids=chunk_ids,
            metadatas=[metadata for _ in chunks]
        )

        # ### MODIFICATION START ###
        # --- Elasticsearch Indexing Logic ---
        logging.info(f"Indexing paper '{paper_id}' in Elasticsearch...")
        self.es_manager.index_paper(paper_id=paper_id, metadata=metadata, content=content)
        # ### MODIFICATION END ###

    # search_by_keywords and get_all_papers remain the same for now
    # We will call them directly from our new hybrid search function in main.py
    def search_by_keywords(self, keywords: List[str], n_results: int = 10) -> List[Dict[str, Any]]:
        query = " ".join(keywords)
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            processed_results = []
            seen_papers = set()
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                paper_id = metadata['paper_id']
                if paper_id in seen_papers:
                    continue
                processed_results.append({
                    'paper_id': paper_id,
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'score': 1 - results['distances'][0][i] # Convert distance to similarity
                })
                seen_papers.add(paper_id)
            return processed_results
        except Exception as e:
            logging.error(f"Error during ChromaDB search: {e}")
            return []

    def get_all_papers(self) -> List[Dict[str, Any]]:
        results = self.collection.get(include=["metadatas", "documents"])
        papers = {}
        for i, metadata in enumerate(results['metadatas']):
            paper_id = metadata.get('paper_id')
            if not paper_id: continue
            if paper_id not in papers:
                papers[paper_id] = {
                    'content': [],
                    'metadata': metadata
                }
            papers[paper_id]['content'].append(results['documents'][i])
        
        return [
            {
                'paper_id': paper_id,
                'content': ' '.join(data['content']),
                'metadata': data['metadata']
            }
            for paper_id, data in papers.items()
        ]

    def remove_paper(self, paper_id: str):
        # ### MODIFICATION START ###
        # Also remove from Elasticsearch
        self.es_manager.delete_paper(paper_id)
        # ### MODIFICATION END ###
        
        results = self.collection.get(where={"paper_id": paper_id})
        if results and results['ids']:
            self.collection.delete(ids=results['ids'])

# ### MODIFICATION START ###
# Updated factory function to accept the ES manager
@st.cache_resource
def get_vector_db(_es_manager: ElasticsearchManager) -> VectorDBManager:
    return VectorDBManager(es_manager=_es_manager)
# ### MODIFICATION END ###