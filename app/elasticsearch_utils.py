# app/elasticsearch_utils.py

import streamlit as st
from elasticsearch import Elasticsearch
from typing import List, Dict, Any

class ElasticsearchManager:
    """
    Manages all interactions with the Elasticsearch cluster, including
    indexing documents and performing searches.
    """
    def __init__(self, cloud_id: str, username: str, password: str):
        try:
            self.es_client = Elasticsearch(
                cloud_id=cloud_id,
                basic_auth=(username, password),
                request_timeout=30
            )
            if not self.es_client.ping():
                raise ConnectionError("Failed to connect to Elasticsearch.")
            self.create_index_if_not_exists("papers")
        except Exception as e:
            st.error(f"Could not connect to Elasticsearch: {e}")
            st.stop()

    def create_index_if_not_exists(self, index_name: str):
        if not self.es_client.indices.exists(index=index_name):
            mapping = {
                "properties": {
                    "title": {"type": "text", "analyzer": "english"},
                    "abstract": {"type": "text", "analyzer": "english"},
                    "content": {"type": "text", "analyzer": "english"},
                    "publication_date": {"type": "date", "format": "yyyy-MM-dd||dd MMM yyyy||epoch_millis"},
                    "url": {"type": "keyword"},
                    "doi_url": {"type": "keyword"},
                    "link": {"type": "keyword"}
                }
            }
            try:
                self.es_client.indices.create(index=index_name, mappings=mapping)
                print(f"Index '{index_name}' created successfully.")
            except Exception as e:
                st.error(f"Failed to create index '{index_name}': {e}")

    # THIS IS THE CRITICAL FIX. THIS FUNCTION IS CORRECT.
    def index_paper(self, paper_id: str, metadata: Dict[str, Any], content: str, index_name: str = "papers"):
        """
        Indexes a single paper document by combining its metadata and content.
        """
        try:
            # Create a single document for indexing by starting with the metadata
            # and adding the full text content.
            document = metadata.copy()
            document['content'] = content
            
            # Now index the complete document, ensuring the 'link' key is saved.
            self.es_client.index(index=index_name, id=paper_id, document=document)
        except Exception as e:
            st.error(f"Failed to index paper {paper_id}: {e}")

    def search_papers(self, keywords: List[str], time_filter: Dict = None, size: int = 10, operator: str = "AND") -> tuple[List[Dict[str, Any]], int]:
        if not keywords:
            return [], 0
        bool_operator = "must" if operator.upper() == "AND" else "should"
        query = {
            "query": {
                "bool": {
                    bool_operator: [
                        # Search across title, abstract, and content for better results.
                        {"multi_match": {"query": keyword, "fields": ["title", "abstract", "content"]}} for keyword in keywords
                    ],
                    "filter": []
                }
            },
            "size": size
        }
        if time_filter:
            query["query"]["bool"]["filter"].append({
                "range": {
                    "publication_date": time_filter
                }
            })
        try:
            response = self.es_client.search(index="papers", body=query)
            hits = response.get('hits', {})
            total = hits.get('total', {})
            
            # Handle different Elasticsearch versions for total count
            if isinstance(total, dict):
                total_count = total.get('value', 0)
            elif isinstance(total, int):
                total_count = total
            else:
                # Fallback: count the actual results
                total_count = len(hits.get('hits', []))
                
            return hits.get('hits', []), total_count
            
        except Exception as e:
            st.error(f"An error occurred during Elasticsearch search: {e}")
            # Return empty results instead of causing app to crash
            return [], 0

@st.cache_resource
def get_es_manager(cloud_id: str, username: str, password: str) -> ElasticsearchManager:
    """
    A cached factory function to get an instance of the ElasticsearchManager.
    """
    es_manager = ElasticsearchManager(cloud_id=cloud_id, username=username, password=password)
    return es_manager