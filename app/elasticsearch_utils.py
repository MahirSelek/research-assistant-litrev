# # app/elasticsearch_utils.py (Final Cloud-Aware Version)
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














# app/elasticsearch_utils.py (Corrected to index URL)

from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError
import logging
from typing import List, Dict, Any
import streamlit as st
import time
import math

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ElasticsearchManager:
    def __init__(self, cloud_id: str, username: str, password: str, index_name: str = "papers"):
        self.cloud_id = cloud_id
        self.username = username
        self.password = password
        self.client = None
        self.index_name = index_name

    def _connect(self):
        if self.client and self.client.ping():
            return
        logging.info("Attempting to connect to Elastic Cloud...")
        retries = 3
        delay = 2
        for i in range(retries):
            try:
                self.client = Elasticsearch(
                    cloud_id=self.cloud_id,
                    basic_auth=(self.username, self.password)
                )
                if self.client.ping():
                    logging.info("Successfully connected to Elasticsearch.")
                    self._create_index_if_not_exists()
                    return
            except Exception as e:
                logging.warning(f"Connection attempt {i+1} failed: {e}. Retrying...")
                time.sleep(delay)
        logging.error("Could not connect to Elasticsearch after several retries.")
        raise ConnectionError("Could not connect to Elasticsearch.")

    def _create_index_if_not_exists(self):
        if not self.client.indices.exists(index=self.index_name):
            # <<< CHANGE 1: ADD 'url' TO THE MAPPING --- >>>
            mapping = {
                "properties": {
                    "title": {"type": "text", "analyzer": "english"},
                    "abstract": {"type": "text", "analyzer": "english"},
                    "content": {"type": "text", "analyzer": "english"},
                    "authors": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "journal": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "publication_date": {"type": "date", "format": "yyyy-MM-dd||yyyy-MM||yyyy||epoch_millis"},
                    "paper_id": {"type": "keyword"},
                    "url": {"type": "keyword"} # This line is new
                }
            }
            self.client.indices.create(index=self.index_name, mappings=mapping)
            logging.info(f"Created Elasticsearch index '{self.index_name}'.")

    def index_paper(self, paper_id: str, metadata: Dict[str, Any], content: str = ""):
        self._connect()
        try:
            # <<< CHANGE 2: ADD 'url' TO THE DOCUMENT BODY --- >>>
            doc_body = {
                "paper_id": paper_id,
                "title": metadata.get('title'),
                "abstract": metadata.get('abstract'),
                "authors": metadata.get('authors'),
                "journal": metadata.get('journal'),
                "publication_date": metadata.get('publication_date'),
                "content": content,
                "url": metadata.get('url') # This line is new
            }
            self.client.index(index=self.index_name, id=paper_id, document=doc_body)
        except Exception as e:
            logging.error(f"Failed to index paper {paper_id} in Elasticsearch: {e}")

    # Using the robust multi-stage fallback search logic
    def search_papers(self, keywords: List[str], time_filter: Dict[str, Any] = None, size: int = 30) -> List[Dict[str, Any]]:
        self._connect()
        if not keywords: 
            return []
        filter_clauses = []
        if time_filter: 
            filter_clauses.append({"range": {"publication_date": time_filter}})
        
        # Stage 1: Strict AND
        logging.info("Executing Stage 1 Search: Strict AND")
        strict_query = {"bool": {"must": [{"multi_match": {"query": keyword, "fields": ["title^3", "abstract^2", "content"]}} for keyword in keywords], "filter": filter_clauses}}
        try:
            response = self.client.search(index=self.index_name, query=strict_query, size=size)
            results = response['hits']['hits']
            if len(results) >= 5:
                logging.info(f"Strict search successful. Found {len(results)} papers.")
                return results
        except Exception:
            results = []

        # Stage 2: Soft AND
        if len(keywords) > 2:
            logging.info("Executing Stage 2 Search: Soft AND")
            min_should_match = math.ceil(len(keywords) * 0.75)
            soft_query = {"bool": {"should": [{"multi_match": {"query": keyword, "fields": ["title^3", "abstract^2", "content"]}} for keyword in keywords], "minimum_should_match": min_should_match, "filter": filter_clauses}}
            try:
                response = self.client.search(index=self.index_name, query=soft_query, size=size)
                results = response['hits']['hits']
                if len(results) > 0:
                    logging.info(f"Soft search successful. Found {len(results)} papers.")
                    return results
            except Exception:
                results = []

        # Stage 3: Lenient OR
        logging.info("Executing Stage 3 Search: Lenient OR")
        lenient_query = {"bool": {"must": {"multi_match": {"query": " ".join(keywords), "fields": ["title^3", "abstract^2", "content"], "type": "best_fields"}}, "filter": filter_clauses}}
        try:
            response = self.client.search(index=self.index_name, query=lenient_query, size=size)
            return response['hits']['hits']
        except Exception as e:
            logging.error(f"Error during lenient search: {e}")
            return []

    def delete_paper(self, paper_id: str):
        self._connect()
        try:
            self.client.delete(index=self.index_name, id=paper_id, ignore=[404])
        except Exception as e: 
            logging.error(f"Failed to delete paper {paper_id} from Elasticsearch: {e}")

@st.cache_resource
def get_es_manager(cloud_id: str, username: str, password: str) -> ElasticsearchManager:
    return ElasticsearchManager(cloud_id=cloud_id, username=username, password=password)