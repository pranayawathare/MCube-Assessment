# Quick fix script - removes duplicates and keeps best data
# Save as quick_fix_duplicates.py

import sqlite3
import sys
from pathlib import Path

def fix_duplicate_units():
    """Remove duplicate units, keeping the one with most complete data"""
    
    db_path = "data/documents.db"
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        print("=== BEFORE CLEANUP ===")
        cursor.execute("SELECT COUNT(*) FROM units")
        before_count = cursor.fetchone()[0]
        print(f"Units before cleanup: {before_count}")
        
        # Find and remove duplicates, keeping the best record for each unit
        print("\n=== REMOVING DUPLICATES ===")
        
        # Strategy: For each unit_number + document_id combination,
        # keep only the record with the highest rent (most complete data)
        cursor.execute("""
            DELETE FROM units 
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id, 
                           ROW_NUMBER() OVER (
                               PARTITION BY document_id, unit_number 
                               ORDER BY rent DESC, total_amount DESC, id DESC
                           ) as rn
                    FROM units
                    WHERE unit_number != ''
                ) ranked 
                WHERE rn = 1
            ) AND unit_number != ''
        """)
        
        duplicates_removed = cursor.rowcount
        print(f"Removed {duplicates_removed} duplicate records")
        
        # Also remove any units with empty unit numbers
        cursor.execute("DELETE FROM units WHERE unit_number = '' OR unit_number IS NULL")
        empty_removed = cursor.rowcount
        print(f"Removed {empty_removed} empty unit records")
        
        conn.commit()
        
        print("\n=== AFTER CLEANUP ===")
        cursor.execute("SELECT COUNT(*) FROM units")
        after_count = cursor.fetchone()[0]
        print(f"Units after cleanup: {after_count}")
        
        # Update document summaries
        print("\n=== UPDATING DOCUMENT SUMMARIES ===")
        
        # Update document statistics based on cleaned units
        cursor.execute("""
            UPDATE documents 
            SET 
                total_units = (
                    SELECT COUNT(*) 
                    FROM units 
                    WHERE units.document_id = documents.id
                ),
                occupied_units = (
                    SELECT COUNT(*) 
                    FROM units 
                    WHERE units.document_id = documents.id 
                    AND units.unit_type = 'Occupied'
                ),
                vacant_units = (
                    SELECT COUNT(*) 
                    FROM units 
                    WHERE units.document_id = documents.id 
                    AND units.unit_type = 'Vacant'
                ),
                total_rent = (
                    SELECT COALESCE(SUM(rent), 0)
                    FROM units 
                    WHERE units.document_id = documents.id
                ),
                total_area = (
                    SELECT COALESCE(SUM(area_sqft), 0)
                    FROM units 
                    WHERE units.document_id = documents.id
                )
        """)
        
        print("✅ Updated document statistics")
        
        # Final verification
        print("\n=== FINAL VERIFICATION ===")
        cursor.execute("""
            SELECT d.file_name, 
                   COUNT(u.id) as units,
                   SUM(CASE WHEN u.unit_type = 'Occupied' THEN 1 ELSE 0 END) as occupied,
                   SUM(CASE WHEN u.unit_type = 'Vacant' THEN 1 ELSE 0 END) as vacant,
                   SUM(u.rent) as total_rent
            FROM documents d
            LEFT JOIN units u ON d.id = u.document_id
            GROUP BY d.id, d.file_name
        """)
        
        total_units = 0
        total_rent = 0
        
        for row in cursor.fetchall():
            print(f"📄 {row[0]}: {row[1]} units ({row[2]} occupied, {row[3]} vacant), ${row[4] or 0:.2f} rent")
            total_units += row[1]
            total_rent += row[4] or 0
        
        print(f"\n🎯 FINAL TOTALS: {total_units} units, ${total_rent:.2f} rent")
        
        # Check for remaining duplicates
        cursor.execute("""
            SELECT unit_number, COUNT(*) as count
            FROM units
            WHERE unit_number != ''
            GROUP BY unit_number, document_id
            HAVING count > 1
        """)
        
        remaining_dups = cursor.fetchall()
        if remaining_dups:
            print(f"⚠️ Still {len(remaining_dups)} duplicate unit numbers")
        else:
            print("✅ No duplicate units remaining!")

if __name__ == "__main__":
    fix_duplicate_units()