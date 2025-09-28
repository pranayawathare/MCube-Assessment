"""
Main application entry point
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.document_parser import DocumentParser
from src.storage_manager import StorageManager
from src.query_interface import QueryInterface

from dotenv import load_dotenv

load_dotenv()

class IntelligentDocumentProcessor:
    def __init__(self, openai_api_key: str = None):
        self.parser = DocumentParser()
        self.storage = StorageManager()
        self.query_interface = QueryInterface(self.storage, openai_api_key)
    
    def process_document(self, file_path: str) -> Dict:
        """Process single document"""
        try:
            document_data = self.parser.parse_document(file_path)
            document_id = self.storage.store_document(document_data)
            self.storage.create_embeddings(document_data)
            
            return {
                'success': True,
                'file_name': document_data['file_name'],
                'total_units': document_data['total_units'],
                'occupied_units': document_data['occupied_units'],
                'vacant_units': document_data['vacant_units'],
                'total_rent': document_data['total_rent']
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'file_path': file_path}
    
    def query(self, question: str) -> Dict:
        """Process query"""
        return self.query_interface.process_query(question)
    
    def interactive_session(self):
        """Interactive query session"""
        print("=== Intelligent Document Processing System ===")
        
        summary = self.storage.get_property_summary()
        print(f"Property Overview:")
        print(f"Total Units: {summary['total_units']}")
        print(f"Occupied: {summary['occupied_units']} | Vacant: {summary['vacant_units']}")
        print(f"Total Rent: ${summary['total_rent']:,.2f}")
        print(f"Total Area: {summary['total_area']:,.0f} sq ft")
        
        print("\nAsk questions (or 'quit' to exit):")
        
        while True:
            try:
                question = input("\nQuestion: ").strip()
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                if not question:
                    continue
                
                result = self.query(question)
                print(f"Answer: {result['answer']}")
                
            except KeyboardInterrupt:
                break

def main():
    parser = argparse.ArgumentParser(description="Intelligent Document Processing System")
    parser.add_argument('--process', nargs='+', help='Process document(s)')
    parser.add_argument('--query', type=str, help='Ask a question')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--openai-key', type=str, help='OpenAI API key')
    
    args = parser.parse_args()
    
    openai_key = args.openai_key or os.getenv('OPENAI_API_KEY')
    processor = IntelligentDocumentProcessor(openai_key)
    
    if args.process:
        for file_path in args.process:
            result = processor.process_document(file_path)
            if result['success']:
                print(f"✅ {result['file_name']}: {result['total_units']} units, ${result['total_rent']:,.2f} rent")
            else:
                print(f"❌ {result['file_path']}: {result['error']}")
    
    if args.query:
        result = processor.query(args.query)
        print(f"Q: {args.query}")
        print(f"A: {result['answer']}")
    
    if args.interactive or (not args.process and not args.query):
        processor.interactive_session()

if __name__ == "__main__":
    main()