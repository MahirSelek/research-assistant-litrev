# app/backend/api.py
"""
Backend API Layer - All business logic separated from frontend
This handles all data processing, AI calls, GCS operations, and authentication
"""

import json
import time
import os
from typing import Dict, List, Any, Optional, Tuple
import datetime
from dateutil import parser as date_parser
from collections import defaultdict

import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import storage
from google.api_core.exceptions import NotFound

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import auth_manager
from gcs_user_storage import GCSUserStorage
from elasticsearch_utils import get_es_manager

class ResearchAssistantAPI:
    def __init__(self, config: Dict[str, Any]):
        """Initialize the backend API with configuration"""
        self.config = config
        
        # Initialize services
        self.gcs_storage = GCSUserStorage(config['gcs_bucket_name'])
        self.es_manager = get_es_manager(
            cloud_id=config['elastic_cloud_id'],
            username=config['elastic_username'],
            password=config['elastic_password']
        )
        
        # Initialize Vertex AI
        vertexai.init(
            project=config['vertexai_project'],
            location=config['vertexai_location']
        )
        self.model = GenerativeModel(config['vertexai_model_id'])
        
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user and return success status and message"""
        return auth_manager.authenticate_user(username, password)
    
    def login_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Login user and set session"""
        return auth_manager.login(username, password)
    
    def logout_user(self):
        """Logout user and clear session"""
        auth_manager.logout()
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid"""
        return auth_manager.is_session_valid()
    
    def get_user_data(self, username: str) -> Dict[str, Any]:
        """Get all user data from GCS"""
        return self.gcs_storage.load_user_data_from_gcs(username)
    
    def save_user_data(self, username: str, data: Dict[str, Any]) -> bool:
        """Save user data to GCS"""
        return self.gcs_storage.save_user_data(username, 'user_preferences', data)
    
    def save_conversation(self, username: str, conversation_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Save conversation to GCS"""
        return self.gcs_storage.save_conversation(username, conversation_id, conversation_data)
    
    def delete_conversation(self, username: str, conversation_id: str) -> bool:
        """Delete conversation from GCS"""
        return self.gcs_storage.delete_conversation(username, conversation_id)
    
    def generate_ai_response(self, prompt: str) -> Optional[str]:
        """Generate AI response using Vertex AI"""
        try:
            generation_config = {"temperature": 0.2, "max_output_tokens": 8192}
            response = self.model.generate_content([prompt], generation_config=generation_config)
            return response.text
        except Exception as e:
            print(f"AI API error: {e}")
            return None
    
    def search_papers(self, keywords: List[str], time_filter_type: str, search_mode: str = "all_keywords") -> Tuple[Optional[str], List[Dict], int]:
        """Search papers and generate analysis"""
        if not keywords:
            return None, [], 0
        
        # Process time filter
        time_filter_dict = self._get_time_filter_dict(time_filter_type)
        
        # Perform search with higher limit for OR searches to get comprehensive results
        n_results = 200 if search_mode == "any_keyword" else 100
        all_papers, total_found = self._perform_hybrid_search(
            keywords, 
            time_filter_dict=None,  # No ES time filtering
            n_results=n_results, 
            max_final_results=15,
            search_mode=search_mode
        )
        
        # Apply GCS-based time filtering if needed
        if time_filter_type != "All time" and all_papers:
            all_papers = self._filter_papers_by_gcs_dates(all_papers, time_filter_type)
            total_found = len(all_papers)
        
        if not all_papers:
            return None, [], 0
        
        # Prepare papers for analysis
        if search_mode == "any_keyword":
            top_papers_for_analysis = all_papers[:15]
            papers_for_references = all_papers
        else:
            top_papers_for_analysis = all_papers
            papers_for_references = all_papers
        
        # Generate analysis
        analysis = self._generate_analysis(top_papers_for_analysis, keywords, search_mode)
        
        # Reload metadata and make citations clickable
        papers_for_references = self._reload_paper_metadata(papers_for_references)
        top_papers_for_analysis = self._reload_paper_metadata(top_papers_for_analysis)
        
        if analysis:
            analysis = self._display_citations_separately(analysis, papers_for_references, top_papers_for_analysis, search_mode)
        
        return analysis, papers_for_references, total_found
    
    def generate_custom_summary(self, uploaded_papers: List[Dict]) -> Optional[str]:
        """Generate summary of uploaded papers"""
        if not uploaded_papers:
            return "No papers uploaded."
        
        # Combine all paper content
        all_content = ""
        paper_titles = []
        
        for paper in uploaded_papers:
            title = paper['metadata'].get('title', 'Unknown Title')
            content = paper.get('content', '')
            paper_titles.append(title)
            all_content += f"\n\n--- {title} ---\n{content}"
        
        # Create summary prompt
        prompt = f"""
        Please provide a comprehensive summary of the following {len(uploaded_papers)} research paper(s):
        
        Papers: {', '.join(paper_titles)}
        
        Content:
        {all_content}
        
        Please provide:
        1. A brief overview of each paper
        2. Key findings and methodologies
        3. Common themes across the papers
        4. Overall conclusions and implications
        
        Keep the summary concise but informative.
        """
        
        return self.generate_ai_response(prompt)
    
    def process_uploaded_pdf(self, pdf_file, filename: str) -> Optional[Dict]:
        """Process uploaded PDF file"""
        try:
            import PyPDF2
            import io
            
            # Get the base name without extension
            pdf_base_name = os.path.splitext(os.path.basename(filename))[0]
            
            # Create basic metadata
            metadata = {
                'title': pdf_base_name,
                'abstract': 'No abstract available',
                'publication_date': '2024-01-01',
                'authors': ['Unknown'],
                'url': '',
                'doi_url': '',
                'link': ''
            }
            
            # Extract PDF content
            pdf_content_bytes = io.BytesIO(pdf_file.getvalue())
            pdf_reader = PyPDF2.PdfReader(pdf_content_bytes)
            paper_content = "".join(page.extract_text() for page in pdf_reader.pages)
            
            if paper_content:
                return {
                    'paper_id': f"uploaded_{pdf_base_name}",
                    'metadata': metadata,
                    'content': paper_content
                }
            return None
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return None
    
    def generate_conversation_title(self, conversation_history: str) -> str:
        """Generate conversation title using AI"""
        prompt = f"Create a concise, 5-word title for this conversation:\n\n---\n{conversation_history}\n---"
        title = self.generate_ai_response(prompt)
        if title:
            return title.strip().replace('"', '')
        return "New Chat"
    
    def get_pdf_from_gcs(self, bucket_name: str, blob_name: str) -> Optional[bytes]:
        """Get PDF bytes from GCS"""
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.download_as_bytes()
        except NotFound:
            print(f"File not found in GCS: {blob_name}")
            return None
        except Exception as e:
            print(f"Failed to download from GCS: {e}")
            return None
    
    # Private helper methods
    def _get_time_filter_dict(self, time_filter_type: str) -> Optional[Dict]:
        """Get time filter dictionary"""
        if time_filter_type == "Current year":
            return {"gte": f"01 Jan 2025", "lte": f"31 Dec 2025"}
        elif time_filter_type == "Last 3 months":
            return {"gte": f"01 Jan 2025"}
        elif time_filter_type == "Last 6 months":
            return {"gte": f"01 Jan 2025"}
        elif time_filter_type in ["January", "February", "March", "April", "May", "June", 
                                 "July", "August", "September", "October", "November", "December"]:
            month_map = {
                "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr", 
                "May": "May", "June": "Jun", "July": "Jul", "August": "Aug", 
                "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec"
            }
            next_month_map = {
                "January": "Feb", "February": "Mar", "March": "Apr", "April": "May", 
                "May": "Jun", "June": "Jul", "July": "Aug", "August": "Sep", 
                "September": "Oct", "October": "Nov", "November": "Dec", "December": "Jan"
            }
            month_abbr = month_map[time_filter_type]
            next_month_abbr = next_month_map[time_filter_type]
            next_year = 2026 if time_filter_type == "December" else 2025
            return {"gte": f"01 {month_abbr} 2025", "lt": f"01 {next_month_abbr} {next_year}"}
        return None
    
    def _perform_hybrid_search(self, keywords: List[str], time_filter_dict: Optional[Dict], 
                              n_results: int, max_final_results: int, search_mode: str) -> Tuple[List[Dict], int]:
        """Perform hybrid search"""
        operator = "AND" if search_mode == "all_keywords" else "OR"
        
        if search_mode == "all_keywords":
            return self._perform_and_search(keywords, time_filter_dict, n_results, 0.005, max_final_results)
        else:
            return self._perform_or_search(keywords, time_filter_dict, n_results)
    
    def _perform_and_search(self, keywords: List[str], time_filter_dict: Optional[Dict], 
                           n_results: int, score_threshold: float, max_final_results: int) -> Tuple[List[Dict], int]:
        """Perform AND search"""
        es_results = self.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results, operator="AND")
        valid_paper_ids = {hit['_id'] for hit in es_results}
        total_papers_found = len(valid_paper_ids)
        
        if not valid_paper_ids:
            return [], 0
        
        fused_scores = defaultdict(lambda: {'score': 0, 'doc': None})
        k = 60
        
        for i, hit in enumerate(es_results):
            rank = i + 1
            paper_id = hit['_id']
            fused_scores[paper_id]['score'] += 1 / (k + rank)
            doc_content = {'paper_id': paper_id, 'metadata': hit['_source'], 'content': hit['_source'].get('content', '')}
            fused_scores[paper_id]['doc'] = doc_content
        
        valid_fused_results = [item for item in fused_scores.values() if item['doc'] is not None]
        sorted_fused_results = sorted(valid_fused_results, key=lambda x: x['score'], reverse=True)
        
        final_paper_list = [
            item['doc'] for item in sorted_fused_results 
            if item['score'] >= score_threshold
        ][:max_final_results]
        
        return final_paper_list, total_papers_found
    
    def _perform_or_search(self, keywords: List[str], time_filter_dict: Optional[Dict], n_results: int) -> Tuple[List[Dict], int]:
        """Perform OR search - get ALL papers that match ANY keyword"""
        # Use a much higher size limit to get comprehensive results
        es_results = self.es_manager.search_papers(keywords, time_filter=time_filter_dict, size=n_results, operator="OR")
        
        all_papers = []
        for hit in es_results:
            paper_id = hit['_id']
            # For OR searches, we don't rely on relevance scoring as much
            # Instead, we prioritize papers that match more keywords
            relevance_score = hit.get('_score', 0.0)
            doc_content = {
                'paper_id': paper_id, 
                'metadata': hit['_source'], 
                'content': hit['_source'].get('content', ''),
                'relevance_score': relevance_score
            }
            all_papers.append(doc_content)
        
        # Sort by relevance score but don't filter by score threshold
        # This ensures we get ALL papers that match ANY keyword
        all_papers.sort(key=lambda x: x.get('relevance_score', 0.0), reverse=True)
        return all_papers, len(all_papers)
    
    def _filter_papers_by_gcs_dates(self, papers: List[Dict], time_filter_type: str) -> List[Dict]:
        """Filter papers by GCS dates"""
        if not papers:
            return papers
        
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(self.config['gcs_bucket_name'])
            
            filtered_papers = []
            for paper in papers:
                paper_id = paper.get('paper_id')
                if paper_id:
                    json_filename = paper_id.rsplit('.', 1)[0] + '.metadata.json'
                    json_blob = bucket.blob(json_filename)
                    
                    if json_blob.exists():
                        try:
                            json_content = json_blob.download_as_string()
                            json_metadata = json.loads(json_content)
                            publication_date = json_metadata.get('publication_date', '')
                            
                            if self._matches_time_filter(publication_date, time_filter_type):
                                filtered_papers.append(paper)
                        except Exception:
                            filtered_papers.append(paper)
                    else:
                        filtered_papers.append(paper)
                else:
                    filtered_papers.append(paper)
            
            return filtered_papers
        except Exception:
            return papers
    
    def _matches_time_filter(self, publication_date: str, time_filter_type: str) -> bool:
        """Check if publication date matches time filter"""
        if not publication_date:
            return False
        
        try:
            parsed_date = date_parser.parse(publication_date)
            
            if time_filter_type == "Current year":
                return parsed_date.year == 2025
            elif time_filter_type in ["Last 3 months", "Last 6 months"]:
                return parsed_date.year == 2025
            elif time_filter_type in ["January", "February", "March", "April", "May", "June", 
                                     "July", "August", "September", "October", "November", "December"]:
                month_map = {
                    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
                    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
                }
                target_month = month_map[time_filter_type]
                return parsed_date.year == 2025 and parsed_date.month == target_month
            
            return True
        except Exception:
            return False
    
    def _generate_analysis(self, papers: List[Dict], keywords: List[str], search_mode: str) -> Optional[str]:
        """Generate analysis using AI"""
        context = "You are a world-class scientific analyst and expert research assistant. Your primary objective is to generate the most detailed and extensive report possible based on the following scientific paper excerpts.\n\n"
        
        for i, result in enumerate(papers):
            meta = result.get('metadata', {})
            title = meta.get('title', 'N/A')
            link = self._get_paper_link(meta)
            content_preview = (meta.get('abstract') or result.get('content') or '')[:4000]
            context += f"SOURCE [{i+1}]:\n"
            context += f"Title: {title}\n"
            context += f"Link: {link}\n"
            context += f"Content: {content_preview}\n---\n\n"
        
        prompt = f"""{context}
---
**CRITICAL TASK:**

You are a world-class scientific analyst. Your task is to generate an exceptionally detailed and extensive multi-part report based *only* on the provided paper sources. The final report should be substantial in length, reflecting a deep synthesis of information from all provided papers.

# Part 1: Thematic Analysis
For the sections "Key Methodological Advances," "Emerging Trends," and "Overall Summary," your analysis **MUST** be exhaustive. Generate at least **three long and detailed paragraphs** or a comprehensive multi-level bulleted list for each of these sections. Do not just list findings; you must deeply synthesize information across multiple sources, explain the significance, compare and contrast approaches, and build a compelling narrative about the state of the research.

   ### Diseases: List the specific diseases, conditions, or traits studied.
   ### Sample Size & Genetic Ancestry: Summarize sample sizes and genetic ancestries mentioned across the papers.
   ### Key Methodological Advances: Provide an in-depth description of significant methods, pipelines, or statistical approaches. Explain *why* they are important advances, how they differ from previous methods, and what new possibilities they unlock.
   ### Emerging Trends: Identify future directions and new research areas. Synthesize recurring themes to explain what trends are emerging in the field. Discuss the implications of these trends for science and medicine.
   ### Overall Summary: Provide a comprehensive, multi-paragraph textual summary of the key findings and clinical implications. This should be a full executive summary, not a brief conclusion.

**CRITICAL INSTRUCTION FOR PART 1:** At the end of every sentence or key finding that you derive from a source, you **MUST** include a citation marker referencing the source's number in brackets. For example: `This new method improves risk prediction [1].` Multiple sources can be cited like `This was observed in several cohorts [2][3].` **IMPORTANT:** Limit citations to a maximum of 3 per sentence. If more than 3 sources support a finding, choose the 3 most relevant or representative sources.

# Part 2: Key Paper Summaries
Identify the top 3-5 most impactful papers from the sources and provide a detailed, one-paragraph summary for each.

**IMPORTANT:** Do NOT create a "References" section. Focus only on the thematic analysis and key paper summaries.

**CRITICAL INSTRUCTION FOR CITATIONS:** At the end of every sentence or key finding that you derive from a source, you **MUST** include a citation marker referencing the source's number in brackets. For example: `This new method improves risk prediction [1].` Multiple sources can be cited like `This was observed in several cohorts [2][3].` **IMPORTANT:** Always separate multiple citations with individual brackets, like `[2][3][4]` NOT `[234]`. **CRUCIAL:** In the Key Paper Summaries section, do NOT add citation numbers to the paper titles - only add citations at the end of the summary paragraphs. **FORMATTING RULE:** All citations MUST be in square brackets [1], [2], [3], etc. - never use unbracketed numbers for citations. **CITATION LIMIT:** Maximum 3 citations per sentence. If more than 3 sources support a finding, choose the 3 most relevant or representative sources.
"""
        return self.generate_ai_response(prompt)
    
    def _get_paper_link(self, metadata: Dict) -> str:
        """Get paper link from metadata"""
        if not isinstance(metadata, dict):
            return "Not available"
        
        for key in ['url', 'link', 'doi_url']:
            link = metadata.get(key)
            if link and isinstance(link, str) and link.startswith('http'):
                return link
        return "Not available"
    
    def _reload_paper_metadata(self, papers: List[Dict]) -> List[Dict]:
        """Reload paper metadata from GCS"""
        if not papers:
            return papers
        
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(self.config['gcs_bucket_name'])
            
            updated_papers = []
            for paper in papers:
                paper_id = paper.get('paper_id')
                if paper_id:
                    json_filename = paper_id.rsplit('.', 1)[0] + '.metadata.json'
                    json_blob = bucket.blob(json_filename)
                    
                    if json_blob.exists():
                        try:
                            json_content = json_blob.download_as_string()
                            json_metadata = json.loads(json_content)
                            
                            updated_metadata = paper.get('metadata', {}).copy()
                            updated_metadata.update(json_metadata)
                            updated_metadata['paper_id'] = paper_id
                            
                            updated_paper = paper.copy()
                            updated_paper['metadata'] = updated_metadata
                            updated_papers.append(updated_paper)
                        except Exception:
                            updated_papers.append(paper)
                    else:
                        updated_papers.append(paper)
                else:
                    updated_papers.append(paper)
            
            return updated_papers
        except Exception:
            return papers
    
    def _display_citations_separately(self, analysis_text: str, papers: List[Dict], 
                                    analysis_papers: List[Dict] = None, search_mode: str = "all_keywords", 
                                    include_references: bool = True) -> str:
        """Make citations clickable and add references section"""
        if not papers:
            return analysis_text
        
        # Make inline citations clickable for analysis papers
        if analysis_papers:
            analysis_text = self._make_inline_citations_clickable(analysis_text, analysis_papers)
        
        if not include_references:
            return analysis_text
        
        citations_section = "\n\n---\n\n### References\n\n"
        
        if search_mode == "any_keyword" and analysis_papers:
            citations_section += "#### References Used in Analysis\n\n"
            
            for i, paper in enumerate(analysis_papers):
                meta = paper.get('metadata', {})
                title = meta.get('title', 'N/A')
                link = self._get_paper_link(meta)
                
                if link != "Not available":
                    citations_section += f"**[{i+1}]** [{title}]({link})\n\n"
                else:
                    citations_section += f"**[{i+1}]** {title}\n\n"
            
            additional_papers = [p for p in papers if p not in analysis_papers]
            if additional_papers:
                citations_section += "#### Additional References Found\n\n"
                start_num = len(analysis_papers) + 1
                
                for i, paper in enumerate(additional_papers):
                    meta = paper.get('metadata', {})
                    title = meta.get('title', 'N/A')
                    link = self._get_paper_link(meta)
                    
                    if link != "Not available":
                        citations_section += f"**[{start_num + i}]** [{title}]({link})\n\n"
                    else:
                        citations_section += f"**[{start_num + i}]** {title}\n\n"
        else:
            for i, paper in enumerate(papers):
                meta = paper.get('metadata', {})
                title = meta.get('title', 'N/A')
                link = self._get_paper_link(meta)
                
                if link != "Not available":
                    citations_section += f"**[{i+1}]** [{title}]({link})\n\n"
                else:
                    citations_section += f"**[{i+1}]** {title}\n\n"
        
        return analysis_text + citations_section
    
    def _make_inline_citations_clickable(self, analysis_text: str, analysis_papers: List[Dict]) -> str:
        """Make inline citations clickable"""
        if not analysis_papers:
            return analysis_text
        
        import re
        
        citation_links = {}
        for i, paper in enumerate(analysis_papers):
            meta = paper.get('metadata', {})
            link = self._get_paper_link(meta)
            if link != "Not available":
                citation_links[i + 1] = link
        
        def replace_citation(match):
            citation_text = match.group(0)
            citation_numbers = re.findall(r'\[(\d+)\]', citation_text)
            
            if len(citation_numbers) > 3:
                citation_numbers = citation_numbers[:3]
            
            result_parts = []
            for num_str in citation_numbers:
                num = int(num_str)
                if num in citation_links:
                    result_parts.append(f'<a href="{citation_links[num]}" target="_blank" class="citation-link">[{num}]</a>')
                else:
                    result_parts.append(f'[{num}]')
            
            return ''.join(result_parts)
        
        citation_pattern = r'\[\d+\](?:\[\d+\])*'
        clickable_text = re.sub(citation_pattern, replace_citation, analysis_text)
        
        return clickable_text
