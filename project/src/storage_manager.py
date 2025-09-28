"""
Storage Manager for SQL database and Qdrant vector database
"""

import sqlite3
import json
import os
import logging
from typing import Dict, List
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, db_path: str = "data/documents.db", qdrant_path: str = "data/qdrant"):
        self.db_path = db_path
        self.qdrant_path = qdrant_path
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(qdrant_path, exist_ok=True)
        
        self._init_database()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Qdrant client (local mode)
        self.qdrant_client = QdrantClient(path=qdrant_path)
        self.collection_name = "documents"
        self._init_qdrant_collection()
    
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT UNIQUE NOT NULL,
                    file_path TEXT,
                    is_scanned BOOLEAN,
                    raw_text TEXT,
                    total_units INTEGER DEFAULT 0,
                    occupied_units INTEGER DEFAULT 0,
                    vacant_units INTEGER DEFAULT 0,
                    total_rent REAL DEFAULT 0.0,
                    total_area REAL DEFAULT 0.0,
                    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    unit_number TEXT,
                    unit_type TEXT,
                    area_sqft REAL DEFAULT 0.0,
                    tenant_name TEXT,
                    rent REAL DEFAULT 0.0,
                    total_amount REAL DEFAULT 0.0,
                    lease_start DATE,
                    lease_end DATE,
                    move_in_date DATE,
                    move_out_date DATE,
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            """)
            
            conn.commit()
    
    def _init_qdrant_collection(self):
        """Initialize Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)
            
            if not collection_exists:
                # Create collection with appropriate vector size
                vector_size = self.embedding_model.get_sentence_embedding_dimension()
                
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection '{self.collection_name}' with vector size {vector_size}")
            else:
                logger.info(f"Qdrant collection '{self.collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {e}")
            raise
    
    def store_document(self, document_data: Dict) -> int:
        """Store document in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert document
            cursor.execute("""
                INSERT OR REPLACE INTO documents 
                (file_name, file_path, is_scanned, raw_text, total_units, 
                 occupied_units, vacant_units, total_rent, total_area)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_data['file_name'],
                document_data['file_path'],
                document_data['is_scanned'],
                document_data['raw_text'],
                document_data['total_units'],
                document_data['occupied_units'],
                document_data['vacant_units'],
                document_data['total_rent'],
                document_data['total_area']
            ))
            
            document_id = cursor.lastrowid
            
            # Delete existing units
            cursor.execute("DELETE FROM units WHERE document_id = ?", (document_id,))
            
            # Insert units
            for unit in document_data['units']:
                cursor.execute("""
                    INSERT INTO units 
                    (document_id, unit_number, unit_type, area_sqft, tenant_name,
                     rent, total_amount, lease_start, lease_end, move_in_date, move_out_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document_id,
                    unit.get('unit', ''),
                    unit.get('unit_type', ''),
                    unit.get('area_sqft', 0),
                    unit.get('tenant_name', ''),
                    unit.get('rent', 0),
                    unit.get('total_amount', 0),
                    unit.get('lease_start') or None,
                    unit.get('lease_end') or None,
                    unit.get('move_in_date') or None,
                    unit.get('move_out_date') or None
                ))
            
            conn.commit()
            return document_id
    
    def create_embeddings(self, document_data: Dict):
        """Create vector embeddings and store in Qdrant"""
        doc_id = document_data['file_name']
        points = []
        
        # Document summary embedding
        summary_text = f"Document {doc_id}: {document_data['total_units']} units, {document_data['occupied_units']} occupied, {document_data['vacant_units']} vacant, ${document_data['total_rent']:.2f} rent, {document_data['total_area']} sqft"
        summary_embedding = self.embedding_model.encode(summary_text)
        
        summary_point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=summary_embedding.tolist(),
            payload={
                'type': 'summary',
                'file_name': doc_id,
                'text': summary_text,
                'total_units': document_data['total_units'],
                'occupied_units': document_data['occupied_units'],
                'vacant_units': document_data['vacant_units'],
                'total_rent': document_data['total_rent'],
                'total_area': document_data['total_area']
            }
        )
        points.append(summary_point)
        
        # Unit embeddings
        for unit in document_data['units']:
            unit_text = f"Unit {unit.get('unit', '')}: {unit.get('unit_type', '')} {unit.get('tenant_name', '')} ${unit.get('rent', 0):.2f} {unit.get('area_sqft', 0)} sqft"
            unit_embedding = self.embedding_model.encode(unit_text)
            
            unit_point = models.PointStruct(
                id=str(uuid.uuid4()),
                vector=unit_embedding.tolist(),
                payload={
                    'type': 'unit',
                    'file_name': doc_id,
                    'text': unit_text,
                    'unit_number': unit.get('unit', ''),
                    'unit_type': unit.get('unit_type', ''),
                    'tenant_name': unit.get('tenant_name', ''),
                    'rent': unit.get('rent', 0),
                    'area_sqft': unit.get('area_sqft', 0)
                }
            )
            points.append(unit_point)
        
        # Insert points into Qdrant
        try:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Stored {len(points)} embeddings in Qdrant for document {doc_id}")
        except Exception as e:
            logger.error(f"Error storing embeddings in Qdrant: {e}")
            raise
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search using Qdrant vector similarity"""
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k,
                score_threshold=0.3  # Only return results with similarity > 0.3
            )
            
            # Convert to our expected format
            results = []
            for result in search_results:
                results.append({
                    'document': result.payload.get('file_name', ''),
                    'similarity': float(result.score),
                    'metadata': result.payload
                })
            
            logger.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_property_summary(self) -> Dict:
        """Get property statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_units,
                    SUM(CASE WHEN unit_type = 'Occupied' THEN 1 ELSE 0 END) as occupied,
                    SUM(CASE WHEN unit_type = 'Vacant' THEN 1 ELSE 0 END) as vacant,
                    SUM(rent) as total_rent,
                    SUM(area_sqft) as total_area
                FROM units
            """)
            
            result = cursor.fetchone()
            total = result[0] or 0
            
            return {
                'total_units': total,
                'occupied_units': result[1] or 0,
                'vacant_units': result[2] or 0,
                'total_rent': result[3] or 0.0,
                'total_area': result[4] or 0.0,
                'occupancy_rate': (result[1] / total * 100) if total > 0 else 0.0
            }
    
    def query_units(self, filters: Dict = None) -> List[Dict]:
        """Query units with filters"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM units"
            params = []
            
            if filters:
                conditions = []
                if 'unit_type' in filters:
                    conditions.append("unit_type = ?")
                    params.append(filters['unit_type'])
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close connections"""
        try:
            if hasattr(self, 'qdrant_client'):
                # Qdrant client doesn't need explicit closing
                pass
        except Exception as e:
            logger.warning(f"Error closing Qdrant client: {e}")