"""
Basic tests for the Intelligent Document Processing System
"""

import unittest
import tempfile
import os
import sys
import sqlite3
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.document_parser import DocumentParser
from src.storage_manager import StorageManager
from src.query_interface import QueryInterface

class TestDocumentParser(unittest.TestCase):
    def setUp(self):
        self.parser = DocumentParser()
    
    def test_initialization(self):
        """Test parser initialization"""
        self.assertIsInstance(self.parser, DocumentParser)
    
    def test_clean_and_validate_units(self):
        """Test unit data cleaning and validation"""
        test_units = [
            {'unit': '01-101', 'rent': 1500.0},
            {'unit': '01-102'},  # Missing data
            {}  # No unit number - should be filtered
        ]
        
        cleaned = self.parser._clean_and_validate_units(test_units)
        
        # Should have 2 valid units (one filtered out)
        self.assertEqual(len(cleaned), 2)
        
        # Check default values are set
        self.assertEqual(cleaned[1]['tenant_name'], 'VACANT')
        self.assertEqual(cleaned[1]['unit_type'], 'Vacant')

class TestStorageManager(unittest.TestCase):
    def setUp(self):
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_vector_dir = tempfile.mkdtemp()
        
        self.storage = StorageManager(
            db_path=self.temp_db.name,
            vector_db_path=self.temp_vector_dir
        )
    
    def tearDown(self):
        # Clean up temporary files
        os.unlink(self.temp_db.name)
        import shutil
        shutil.rmtree(self.temp_vector_dir)
    
    def test_database_initialization(self):
        """Test database tables are created properly"""
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn('documents', tables)
            self.assertIn('units', tables)
    
    def test_store_document(self):
        """Test document storage functionality"""
        test_document = {
            'file_name': 'test.pdf',
            'file_path': '/test/path.pdf',
            'is_scanned': False,
            'raw_text': 'Test content',
            'units': [{
                'unit': '01-101',
                'unit_type': 'Occupied',
                'tenant_name': 'John Doe',
                'rent': 1500.0,
                'total_amount': 1500.0,
                'area_sqft': 850
            }],
            'total_units': 1,
            'occupied_units': 1,
            'vacant_units': 0,
            'total_rent': 1500.0,
            'total_area': 850.0
        }
        
        doc_id = self.storage.store_document(test_document)
        self.assertIsInstance(doc_id, int)
        self.assertGreater(doc_id, 0)
        
        # Verify document was stored
        documents = self.storage.get_all_documents()
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]['file_name'], 'test.pdf')
    
    def test_property_summary(self):
        """Test property summary calculation"""
        # Store test document first
        test_document = {
            'file_name': 'test.pdf',
            'file_path': '/test/path.pdf',
            'is_scanned': False,
            'raw_text': 'Test content',
            'units': [
                {
                    'unit': '01-101',
                    'unit_type': 'Occupied',
                    'rent': 1500.0,
                    'area_sqft': 850
                },
                {
                    'unit': '01-102',
                    'unit_type': 'Vacant',
                    'rent': 0.0,
                    'area_sqft': 900
                }
            ],
            'total_units': 2,
            'occupied_units': 1,
            'vacant_units': 1,
            'total_rent': 1500.0,
            'total_area': 1750.0
        }
        
        self.storage.store_document(test_document)
        
        summary = self.storage.get_property_summary()
        
        self.assertEqual(summary['total_units'], 2)
        self.assertEqual(summary['occupied_units'], 1)
        self.assertEqual(summary['vacant_units'], 1)
        self.assertEqual(summary['total_rent'], 1500.0)
        self.assertEqual(summary['occupancy_rate'], 50.0)

class TestQueryInterface(unittest.TestCase):
    def setUp(self):
        # Create temporary storage
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_vector_dir = tempfile.mkdtemp()
        
        self.storage = StorageManager(
            db_path=self.temp_db.name,
            vector_db_path=self.temp_vector_dir
        )
        
        self.query_interface = QueryInterface(self.storage)
        
        # Add test data
        test_document = {
            'file_name': 'test.pdf',
            'file_path': '/test/path.pdf',
            'is_scanned': False,
            'raw_text': 'Test content',
            'units': [{
                'unit': '01-101',
                'unit_type': 'Occupied',
                'tenant_name': 'John Doe',
                'rent': 1500.0,
                'total_amount': 1500.0,
                'area_sqft': 850
            }],
            'total_units': 1,
            'occupied_units': 1,
            'vacant_units': 0,
            'total_rent': 1500.0,
            'total_area': 850.0
        }
        
        self.storage.store_document(test_document)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
        import shutil
        shutil.rmtree(self.temp_vector_dir)
    
    def test_rule_based_queries(self):
        """Test rule-based query processing"""
        # Test total units query
        result = self.query_interface.process_query("What is the total number of units?")
        
        self.assertIsInstance(result, dict)
        self.assertIn('answer', result)
        self.assertIn('confidence', result)
        self.assertGreater(result['confidence'], 0.5)
        self.assertIn('1 units', result['answer'])
    
    def test_query_patterns(self):
        """Test various query patterns"""
        test_queries = [
            "How many units are occupied?",
            "What is the total rent?",
            "Show me the total area",
            "What is the occupancy rate?"
        ]
        
        for query in test_queries:
            result = self.query_interface.process_query(query)
            self.assertIsInstance(result, dict)
            self.assertIn('answer', result)
            self.assertGreater(len(result['answer']), 0)
    
    def test_suggested_queries(self):
        """Test suggested queries functionality"""
        suggestions = self.query_interface.get_suggested_queries()
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # All suggestions should be strings
        for suggestion in suggestions:
            self.assertIsInstance(suggestion, str)
            self.assertGreater(len(suggestion), 0)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_vector_dir = tempfile.mkdtemp()
        
        # Initialize complete system
        self.parser = DocumentParser()
        self.storage = StorageManager(
            db_path=self.temp_db.name,
            vector_db_path=self.temp_vector_dir
        )
        self.query_interface = QueryInterface(self.storage)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
        import shutil
        shutil.rmtree(self.temp_vector_dir)
    
    @patch('fitz.open')
    def test_end_to_end_processing(self, mock_fitz):
        """Test complete document processing workflow"""
        # Mock PyMuPDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = """
        Unit 01-101 Occupied John Doe $1,500.00
        Unit 01-102 Vacant VACANT $0.00
        """
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__ = lambda x: 1
        mock_fitz.return_value = mock_doc
        
        # Process document
        result = self.parser.parse_document("test.pdf")
        
        # Store document
        doc_id = self.storage.store_document(result)
        self.assertIsInstance(doc_id, int)
        
        # Create embeddings
        embedding_id = self.storage.create_embeddings(result)
        self.assertIsNotNone(embedding_id)
        
        # Query the system
        query_result = self.query_interface.process_query("How many units are there?")
        
        self.assertIn('answer', query_result)
        self.assertGreater(query_result['confidence'], 0)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)