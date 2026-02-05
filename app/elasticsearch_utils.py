# app/elasticsearch_utils.py
# suitable for Elasticsearch 8.0.0 and main.py v2

import streamlit as st
from elasticsearch import Elasticsearch
from typing import List, Dict, Any

class ElasticsearchManager:
    """
    Manages all interactions with the Elasticsearch cluster, including
    indexing documents and performing searches.
    Supports both Serverless (hosts + api_key) and Hosted (cloud_id + username/password) deployments.
    """
    def __init__(self, cloud_id: str = None, hosts: list = None, username: str = None, password: str = None, api_key: str = None):
        try:
            # Support both Serverless (hosts + api_key) and Hosted (cloud_id + username/password)
            if hosts and api_key:
                # Serverless: Use endpoint URL with API key
                print(f"Connecting to Serverless Elasticsearch at: {hosts[0]}")
                self.es_client = Elasticsearch(
                    hosts=hosts,
                    api_key=api_key,
                    request_timeout=30
                )
            elif cloud_id and username and password:
                # Hosted: Use Cloud ID with username/password
                print(f"Connecting to Hosted Elasticsearch with Cloud ID")
                self.es_client = Elasticsearch(
                    cloud_id=cloud_id,
                    basic_auth=(username, password),
                    request_timeout=30
                )
            else:
                raise ValueError("Must provide either (hosts + api_key) for Serverless or (cloud_id + username + password) for Hosted")
            
            if not self.es_client.ping():
                raise ConnectionError("Failed to connect to Elasticsearch.")
            print("✓ Successfully connected to Elasticsearch")
            self.create_index_if_not_exists("papers")
        except Exception as e:
            error_msg = f"Could not connect to Elasticsearch: {e}"
            print(f"✗ {error_msg}")
            st.error(error_msg)
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
            
            # Complete document indexing, ensuring the 'link' key is saved.
            self.es_client.index(index=index_name, id=paper_id, document=document)
        except Exception as e:
            st.error(f"Failed to index paper {paper_id}: {e}")

    def search_papers(self, keywords: List[str], time_filter: Dict = None, size: int = 10, operator: str = "AND") -> List[Dict[str, Any]]:
        if not keywords:
            return []
        bool_operator = "must" if operator.upper() == "AND" else "should"
        
        # The base query structure
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
        
        # For OR queries, we need to specify minimum_should_match to ensure at least one keyword matches
        if operator.upper() == "OR":
            query["query"]["bool"]["minimum_should_match"] = 1
        if time_filter:
            query["query"]["bool"]["filter"].append({
                "range": {
                    "publication_date": time_filter
                }
            })
        try:
            response = self.es_client.search(index="papers", body=query)
            return response.get('hits', {}).get('hits', [])
        except Exception as e:
            st.error(f"An error occurred during Elasticsearch search: {e}")
            return []

@st.cache_resource
def get_es_manager(cloud_id: str = None, hosts: list = None, username: str = None, password: str = None, api_key: str = None) -> ElasticsearchManager:
    """
    A cached factory function to get an instance of the ElasticsearchManager.
    Supports both Serverless (hosts + api_key) and Hosted (cloud_id + username + password).
    """
    es_manager = ElasticsearchManager(
        cloud_id=cloud_id, 
        hosts=hosts, 
        username=username, 
        password=password, 
        api_key=api_key
    )
    return es_manager