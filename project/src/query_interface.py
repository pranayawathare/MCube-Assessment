"""
Query Interface for natural language processing
"""

import re
import os
import logging
from typing import Dict, List, Optional

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from storage_manager import StorageManager

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryInterface:
    def __init__(self, storage_manager: StorageManager, openai_api_key: Optional[str] = None):
        self.storage = storage_manager
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        self.llm = None
        if LANGCHAIN_AVAILABLE and self.openai_api_key:
            try:
                self.llm = ChatOpenAI(
                    api_key=self.openai_api_key,
                    model="gpt-3.5-turbo",
                    temperature=0.1
                )
            except Exception as e:
                logger.warning(f"LLM initialization failed: {e}")
        
        self.patterns = {
            'total_units': [r'(?i).*total.*units?.*', r'(?i).*how many.*units?.*'],
            'total_area': [r'(?i).*total.*(?:square.*feet?|sq.*ft|area).*'],
            'total_rent': [r'(?i).*total.*rent.*'],
            'occupied_units': [r'(?i).*occupied.*units?.*'],
            'vacant_units': [r'(?i).*vacant.*units?.*'],
            'occupancy_rate': [r'(?i).*occupancy.*rate.*']
        }
    
    def process_query(self, query: str) -> Dict:
        """Process natural language query"""
        # Try rule-based first
        result = self._rule_based_query(query)
        if result['confidence'] > 0.7:
            return result
        
        # Try LLM if available
        if self.llm:
            return self._llm_query(query)
        
        # Fallback to semantic search
        return self._semantic_search_query(query)
    
    def _rule_based_query(self, query: str) -> Dict:
        """Rule-based query processing"""
        summary = self.storage.get_property_summary()
        
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    if intent == 'total_units':
                        return {
                            'query': query,
                            'answer': f"The property has {summary['total_units']} total units.",
                            'confidence': 0.9,
                            'data': {'total_units': summary['total_units']}
                        }
                    elif intent == 'total_area':
                        return {
                            'query': query,
                            'answer': f"The total square footage is {summary['total_area']:,.0f} sq ft.",
                            'confidence': 0.9,
                            'data': {'total_area': summary['total_area']}
                        }
                    elif intent == 'total_rent':
                        return {
                            'query': query,
                            'answer': f"The total rent is ${summary['total_rent']:,.2f}.",
                            'confidence': 0.9,
                            'data': {'total_rent': summary['total_rent']}
                        }
                    elif intent == 'occupied_units':
                        return {
                            'query': query,
                            'answer': f"There are {summary['occupied_units']} occupied units out of {summary['total_units']} total.",
                            'confidence': 0.9,
                            'data': {'occupied_units': summary['occupied_units'], 'total_units': summary['total_units']}
                        }
                    elif intent == 'vacant_units':
                        return {
                            'query': query,
                            'answer': f"There are {summary['vacant_units']} vacant units out of {summary['total_units']} total.",
                            'confidence': 0.9,
                            'data': {'vacant_units': summary['vacant_units'], 'total_units': summary['total_units']}
                        }
                    elif intent == 'occupancy_rate':
                        return {
                            'query': query,
                            'answer': f"The occupancy rate is {summary['occupancy_rate']:.1f}%.",
                            'confidence': 0.9,
                            'data': {'occupancy_rate': summary['occupancy_rate']}
                        }
        
        return {'query': query, 'answer': '', 'confidence': 0.0, 'data': {}}
    
    def _llm_query(self, query: str) -> Dict:
        """LLM-based query processing"""
        try:
            summary = self.storage.get_property_summary()
            search_results = self.storage.semantic_search(query, top_k=3)
            
            context = f"""Property Summary:
- Total Units: {summary['total_units']}
- Occupied Units: {summary['occupied_units']}
- Vacant Units: {summary['vacant_units']}
- Total Rent: ${summary['total_rent']:,.2f}
- Total Area: {summary['total_area']:,.0f} sq ft
- Occupancy Rate: {summary['occupancy_rate']:.1f}%

Relevant search results: {search_results[:2]}"""
            
            messages = [
                SystemMessage(content="You are a property data analyst. Answer questions accurately based on the provided data."),
                HumanMessage(content=f"Context: {context}\n\nQuestion: {query}")
            ]
            
            response = self.llm.invoke(messages)
            
            return {
                'query': query,
                'answer': response.content,
                'confidence': 0.8,
                'data': summary
            }
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return self._semantic_search_query(query)
    
    def _semantic_search_query(self, query: str) -> Dict:
        """Semantic search fallback"""
        results = self.storage.semantic_search(query, top_k=3)
        
        if not results:
            return {
                'query': query,
                'answer': "I couldn't find relevant information for your query.",
                'confidence': 0.1,
                'data': {}
            }
        
        answer = "Based on the available data:\n"
        for result in results[:2]:
            meta = result['metadata']
            if meta['type'] == 'summary':
                answer += f"Total: {meta['total_units']} units ({meta['occupied_units']} occupied, {meta['vacant_units']} vacant)\n"
            elif meta['type'] == 'unit':
                answer += f"Unit {meta['unit_number']}: {meta['unit_type']}, ${meta['rent']:.2f}\n"
        
        return {
            'query': query,
            'answer': answer,
            'confidence': 0.6,
            'data': results[0]['metadata'] if results else {}
        }