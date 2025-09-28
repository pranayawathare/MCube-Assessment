"""
Intelligent Document Processing System
A comprehensive AI/ML system for processing financial documents
"""

__version__ = "1.0.0"
__author__ = "MCube Financial - Senior AI/ML Engineer Assessment"

from .document_parser import DocumentParser
from .storage_manager import StorageManager  
from .query_interface import QueryInterface

__all__ = [
    'DocumentParser',
    'StorageManager', 
    'QueryInterface'
]