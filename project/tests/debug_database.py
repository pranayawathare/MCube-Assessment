# Create a debug script to check database contents
# Save as debug_database.py

import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def debug_database():
    db_path = "data/documents.db"
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check documents table
        print("=== DOCUMENTS TABLE ===")
        cursor.execute("SELECT id, file_name, total_units, occupied_units, vacant_units, total_rent FROM documents")
        documents = cursor.fetchall()
        
        for doc in documents:
            print(f"ID: {doc[0]}, File: {doc[1]}, Units: {doc[2]}, Occupied: {doc[3]}, Vacant: {doc[4]}, Rent: ${doc[5]:.2f}")
        
        print(f"\nTotal documents in database: {len(documents)}")
        
        # Check units table
        print("\n=== UNITS TABLE SUMMARY ===")
        cursor.execute("SELECT COUNT(*) FROM units")
        total_units = cursor.fetchone()[0]
        print(f"Total units in database: {total_units}")
        
        # Check units by document
        cursor.execute("""
            SELECT d.file_name, COUNT(u.id) as unit_count, SUM(u.rent) as total_rent
            FROM documents d
            LEFT JOIN units u ON d.id = u.document_id
            GROUP BY d.id, d.file_name
        """)
        
        print("\n=== UNITS BY DOCUMENT ===")
        for row in cursor.fetchall():
            print(f"Document: {row[0]}, Units: {row[1]}, Rent: ${row[2] or 0:.2f}")
        
        # Check for duplicates
        cursor.execute("""
            SELECT unit_number, COUNT(*) as count
            FROM units
            WHERE unit_number != ''
            GROUP BY unit_number
            HAVING count > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"\n=== DUPLICATE UNITS (Top 10) ===")
            for unit, count in duplicates:
                print(f"Unit {unit}: {count} duplicates")
        else:
            print("\n=== NO DUPLICATE UNITS FOUND ===")

if __name__ == "__main__":
    debug_database()