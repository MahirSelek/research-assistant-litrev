# # app/elasticsearch_utils.py (Final Cloud-Aware Version) - MOST IMPORTANT
# # This code piece part of only with inline clickable links


# from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError
# import logging
# from typing import List, Dict, Any
# import streamlit as st
# import time

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# class ElasticsearchManager:
#     def __init__(self, cloud_id: str, username: str, password: str, index_name: str = "papers"):
#         """Initializes the manager for a secure Elastic Cloud connection."""
#         self.cloud_id = cloud_id
#         self.username = username
#         self.password = password
#         self.client = None
#         self.index_name = index_name

#     def _connect(self):
#         """Establishes a connection to Elastic Cloud using cloud_id and basic_auth."""
#         if self.client and self.client.ping():
#             return

#         logging.info("Attempting to connect to Elastic Cloud...")
#         retries = 3
#         delay = 2
#         for i in range(retries):
#             try:
#                 self.client = Elasticsearch(
#                     cloud_id=self.cloud_id,
#                     basic_auth=(self.username, self.password)
#                 )
#                 if self.client.ping():
#                     logging.info("Successfully connected to Elasticsearch.")
#                     self._create_index_if_not_exists()
#                     return
#             except Exception as e:
#                 logging.warning(f"Connection attempt {i+1} failed: {e}. Retrying...")
#                 time.sleep(delay)
        
#         logging.error("Could not connect to Elasticsearch after several retries.")
#         raise ConnectionError("Could not connect to Elasticsearch.")

#     def _create_index_if_not_exists(self):
#         if not self.client.indices.exists(index=self.index_name):
#             mapping = { "properties": { "title": {"type": "text", "analyzer": "english"}, "abstract": {"type": "text", "analyzer": "english"}, "content": {"type": "text", "analyzer": "english"}, "authors": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}, "journal": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}, "publication_date": {"type": "date", "format": "yyyy-MM-dd||yyyy-MM||yyyy||epoch_millis"}, "paper_id": {"type": "keyword"} } }
#             self.client.indices.create(index=self.index_name, mappings=mapping)
#             logging.info(f"Created Elasticsearch index '{self.index_name}'.")

#     def index_paper(self, paper_id: str, metadata: Dict[str, Any], content: str = ""):
#         self._connect()
#         try:
#             doc_body = { "paper_id": paper_id, "title": metadata.get('title'), "abstract": metadata.get('abstract'), "authors": metadata.get('authors'), "journal": metadata.get('journal'), "publication_date": metadata.get('publication_date'), "content": content }
#             self.client.index(index=self.index_name, id=paper_id, document=doc_body)
#         except Exception as e: 
#             logging.error(f"Failed to index paper {paper_id} in Elasticsearch: {e}")

#     def search_papers(self, keywords: List[str], time_filter: Dict[str, Any] = None, size: int = 10) -> List[Dict[str, Any]]:
#         self._connect()
#         if not keywords: return []
#         keyword_query = { "multi_match": { "query": " ".join(keywords), "fields": ["title^3", "abstract^2", "content", "authors", "journal"], "type": "best_fields" } }
#         filter_clauses = []
#         if time_filter: filter_clauses.append({"range": {"publication_date": time_filter}})
#         query = { "bool": { "must": keyword_query, "filter": filter_clauses if filter_clauses else [] } }
#         try:
#             response = self.client.search(index=self.index_name, query=query, size=size)
#             return [hit for hit in response['hits']['hits']]
#         except Exception as e:
#             logging.error(f"Error searching Elasticsearch: {e}")
#             return []

#     def delete_paper(self, paper_id: str):
#         self._connect()
#         try:
#             self.client.delete(index=self.index_name, id=paper_id, ignore=[404])
#         except Exception as e: 
#             logging.error(f"Failed to delete paper {paper_id} from Elasticsearch: {e}")

# @st.cache_resource
# def get_es_manager(cloud_id: str, username: str, password: str) -> ElasticsearchManager:
#     """Returns a cached instance of the ElasticsearchManager for cloud connection."""
#     return ElasticsearchManager(cloud_id=cloud_id, username=username, password=password)














# 01/09 Deneme:

# # app/elasticsearch_utils.py

# import streamlit as st
# from elasticsearch import Elasticsearch
# from typing import List, Dict, Any

# # <<< FIX: Renamed class from ESManager to ElasticsearchManager to match the import in your other files.
# class ElasticsearchManager:
#     """
#     Manages all interactions with the Elasticsearch cluster, including
#     indexing documents and performing searches.
#     """
#     def __init__(self, cloud_id: str, username: str, password: str):
#         """
#         Initializes the Elasticsearch client.

#         Args:
#             cloud_id (str): The Cloud ID for the Elasticsearch deployment.
#             username (str): The username for authentication.
#             password (str): The password for authentication.
#         """
#         try:
#             self.es_client = Elasticsearch(
#                 cloud_id=cloud_id,
#                 basic_auth=(username, password),
#                 request_timeout=30
#             )
#             # Verify the connection is alive
#             if not self.es_client.ping():
#                 raise ConnectionError("Failed to connect to Elasticsearch.")
            
#             # Ensure the 'papers' index exists with the correct mapping
#             self.create_index_if_not_exists("papers")

#         except Exception as e:
#             st.error(f"Could not connect to Elasticsearch: {e}")
#             st.stop()

#     def create_index_if_not_exists(self, index_name: str):
#         """
#         Creates an index with a specific mapping if it doesn't already exist.
#         This ensures fields like dates are correctly interpreted.
#         """
#         if not self.es_client.indices.exists(index=index_name):
#             mapping = {
#                 "properties": {
#                     "title": {"type": "text"},
#                     "content": {"type": "text"},
#                     "publication_date": {"type": "date", "format": "yyyy-MM-dd||epoch_millis"},
#                     "url": {"type": "keyword"},
#                     "doi_url": {"type": "keyword"},
#                     "link": {"type": "keyword"}
#                 }
#             }
#             try:
#                 self.es_client.indices.create(index=index_name, mappings=mapping)
#                 print(f"Index '{index_name}' created successfully.")
#             except Exception as e:
#                 st.error(f"Failed to create index '{index_name}': {e}")


#     def index_paper(self, paper_id: str, document: Dict[str, Any], index_name: str = "papers"):
#         """
#         Indexes a single paper document.

#         Args:
#             paper_id (str): The unique ID for the paper.
#             document (Dict[str, Any]): The paper data to be indexed.
#             index_name (str): The name of the index to add the paper to.
#         """
#         try:
#             self.es_client.index(index=index_name, id=paper_id, document=document)
#         except Exception as e:
#             st.error(f"Failed to index paper {paper_id}: {e}")

#     def search_papers(self, keywords: List[str], time_filter: Dict = None, size: int = 10, operator: str = "AND") -> List[Dict[str, Any]]:
#         """
#         Searches for papers using keywords with support for AND/OR logic
#         across multiple fields (title and content).

#         Args:
#             keywords (List[str]): A list of keywords to search for.
#             time_filter (Dict, optional): A dictionary for date range filtering. Defaults to None.
#             size (int, optional): The number of results to return. Defaults to 10.
#             operator (str, optional): The boolean logic to use ('AND' or 'OR'). Defaults to "OR".

#         Returns:
#             List[Dict[str, Any]]: A list of search result hits.
#         """
#         if not keywords:
#             return []

#         bool_operator = "must" if operator.upper() == "AND" else "should"

#         query = {
#             "query": {
#                 "bool": {
                   
#                     bool_operator: [
#                         {"multi_match": {"query": keyword, "fields": ["title", "content"]}} for keyword in keywords
#                     ],
#                     "filter": []
#                 }
#             },
#             "size": size
#         }

#         # Add the time filter if it's provided
#         if time_filter:
#             query["query"]["bool"]["filter"].append({
#                 "range": {
#                     "publication_date": time_filter
#                 }
#             })

#         try:
#             response = self.es_client.search(index="papers", body=query)
#             return response.get('hits', {}).get('hits', [])
#         except Exception as e:
#             st.error(f"An error occurred during Elasticsearch search: {e}")
#             return []

# @st.cache_resource
# # <<< FIX: Updated the return type hint to match the new class name.
# def get_es_manager(cloud_id: str, username: str, password: str) -> ElasticsearchManager:
#     """
#     A cached factory function to get an instance of the ElasticsearchManager.
#     Using st.cache_resource ensures the connection is established only once.
#     """
#     es_manager = ElasticsearchManager(cloud_id=cloud_id, username=username, password=password)
#     return es_manager

















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

    def search_papers(self, keywords: List[str], time_filter: Dict = None, size: int = 10, operator: str = "AND") -> List[Dict[str, Any]]:
        if not keywords:
            return []
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
            return response.get('hits', {}).get('hits', [])
        except Exception as e:
            st.error(f"An error occurred during Elasticsearch search: {e}")
            return []

@st.cache_resource
def get_es_manager(cloud_id: str, username: str, password: str) -> ElasticsearchManager:
    """
    A cached factory function to get an instance of the ElasticsearchManager.
    """
    es_manager = ElasticsearchManager(cloud_id=cloud_id, username=username, password=password)
    return es_manager