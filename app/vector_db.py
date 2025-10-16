# app/vector_db.py

# Vector database functionality is currently disabled
# This file contains stub functions to prevent import errors

from typing import List, Dict, Any
import streamlit as st
from elasticsearch_utils import ElasticsearchManager

class VectorDBManager:
    """
    Stub class for VectorDBManager when ChromaDB is disabled.
    All methods return empty results or do nothing.
    """
    def __init__(self, es_manager: ElasticsearchManager, gcs_bucket_name: str):
        self.es_manager = es_manager
        self.gcs_bucket_name = gcs_bucket_name

    def add_paper(self, paper_id: str, content: str, metadata: Dict[str, Any]):
        """Stub method - does nothing when ChromaDB is disabled."""
        pass

    def search_by_keywords(self, keywords: List[str], n_results: int = 10) -> List[Dict[str, Any]]:
        """Stub method - returns empty list when ChromaDB is disabled."""
        return []

    def get_all_papers(self) -> List[Dict[str, Any]]:
        """Stub method - returns empty list when ChromaDB is disabled."""
        return []

    def remove_paper(self, paper_id: str):
        """Stub method - does nothing when ChromaDB is disabled."""
        pass

    def get_db_status(self) -> dict:
        """Stub method - returns inactive status."""
        return {"status": "Inactive", "message": "ChromaDB is disabled"}

    def update_paper_metadata(self, paper_id: str, new_metadata: Dict[str, Any]):
        """Stub method - does nothing when ChromaDB is disabled."""
        pass

# The factory function that connects everything together from secrets
@st.cache_resource
def get_vector_db(_es_manager: ElasticsearchManager) -> VectorDBManager:
    """Gets a cached instance of the VectorDBManager stub."""
    gcs_bucket_name = st.secrets["app_config"]["gcs_bucket_name"]
    return VectorDBManager(es_manager=_es_manager, gcs_bucket_name=gcs_bucket_name)









