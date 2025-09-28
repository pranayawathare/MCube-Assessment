# Audit script to check all required fields are being captured
# Save as data_field_audit.py

import sqlite3
import sys
from pathlib import Path

def audit_extracted_fields():
    """Audit all required fields from the assessment"""
    
    db_path = "data/documents.db"
    
    # Required fields from assessment
    required_fields = [
        "Unit",
        "Unit Type", 
        "Area / Square Ft",
        "Tenant Name",
        "Rent",
        "Total Amount",
        "Lease Start",
        "Lease End", 
        "Move In Date",
        "Move Out Date"
    ]
    
    # Database field mapping
    db_field_mapping = {
        "Unit": "unit_number",
        "Unit Type": "unit_type", 
        "Area / Square Ft": "area_sqft",
        "Tenant Name": "tenant_name",
        "Rent": "rent",
        "Total Amount": "total_amount",
        "Lease Start": "lease_start",
        "Lease End": "lease_end",
        "Move In Date": "move_in_date", 
        "Move Out Date": "move_out_date"
    }
    
    print("🔍 COMPLETE DATA FIELD EXTRACTION AUDIT")
    print("=" * 50)
    print("Assessment Requirements vs Current Extraction\n")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get total units for percentage calculations
        cursor.execute("SELECT COUNT(*) FROM units")
        total_units = cursor.fetchone()[0]
        print(f"Total Units to Analyze: {total_units}\n")
        
        # Analyze each required field
        field_results = {}
        
        for req_field in required_fields:
            db_field = db_field_mapping[req_field]
            
            print(f"📊 {req_field} (DB: {db_field})")
            
            # Count non-empty values
            cursor.execute(f"""
                SELECT COUNT(*) FROM units 
                WHERE {db_field} IS NOT NULL 
                AND {db_field} != ''
                AND {db_field} != 0
            """)
            populated_count = cursor.fetchone()[0]
            
            # Get sample values
            cursor.execute(f"""
                SELECT {db_field} FROM units 
                WHERE {db_field} IS NOT NULL 
                AND {db_field} != ''
                AND {db_field} != 0
                LIMIT 5
            """)
            samples = [row[0] for row in cursor.fetchall()]
            
            coverage_pct = (populated_count / total_units * 100) if total_units > 0 else 0
            
            print(f"   Coverage: {populated_count}/{total_units} ({coverage_pct:.1f}%)")
            
            if samples:
                print(f"   Samples: {samples[:3]}...")
                status = "✅ CAPTURED" if coverage_pct > 20 else "⚠️ PARTIAL" if coverage_pct > 0 else "❌ MISSING"
            else:
                print(f"   Samples: No data found")
                status = "❌ MISSING"
            
            print(f"   Status: {status}")
            print()
            
            field_results[req_field] = {
                'coverage': coverage_pct,
                'count': populated_count,
                'status': status,
                'samples': samples
            }
        
        # Overall assessment
        print("📋 FIELD EXTRACTION SUMMARY")
        print("=" * 30)
        
        captured_fields = sum(1 for r in field_results.values() if r['coverage'] > 20)
        partial_fields = sum(1 for r in field_results.values() if 0 < r['coverage'] <= 20)
        missing_fields = sum(1 for r in field_results.values() if r['coverage'] == 0)
        
        print(f"✅ Fully Captured: {captured_fields}/10 fields")
        print(f"⚠️ Partially Captured: {partial_fields}/10 fields") 
        print(f"❌ Missing: {missing_fields}/10 fields")
        
        total_coverage = (captured_fields + partial_fields * 0.5) / 10 * 100
        print(f"\n🎯 Overall Field Coverage: {total_coverage:.1f}%")
        
        # Detailed breakdown by document
        print(f"\n📄 BREAKDOWN BY DOCUMENT")
        print("=" * 25)
        
        cursor.execute("""
            SELECT d.file_name, d.id
            FROM documents d
            ORDER BY d.file_name
        """)
        
        for doc_name, doc_id in cursor.fetchall():
            print(f"\n📄 {doc_name}")
            
            cursor.execute("SELECT COUNT(*) FROM units WHERE document_id = ?", (doc_id,))
            doc_units = cursor.fetchone()[0]
            print(f"   Units: {doc_units}")
            
            # Check key fields for this document
            key_fields = ["unit_number", "rent", "unit_type", "tenant_name"]
            for field in key_fields:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM units 
                    WHERE document_id = ? 
                    AND {field} IS NOT NULL 
                    AND {field} != ''
                    AND {field} != 0
                """, (doc_id,))
                
                field_count = cursor.fetchone()[0]
                field_pct = (field_count / doc_units * 100) if doc_units > 0 else 0
                
                status_icon = "✅" if field_pct > 50 else "⚠️" if field_pct > 0 else "❌"
                print(f"   {field}: {field_count}/{doc_units} ({field_pct:.1f}%) {status_icon}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("=" * 18)
        
        priority_missing = []
        for field, result in field_results.items():
            if result['coverage'] < 20:
                priority_missing.append(field)
        
        if priority_missing:
            print("🔧 Fields needing improvement:")
            for field in priority_missing:
                print(f"   - {field}")
                
            print(f"\n🛠️ Suggested improvements:")
            if "Lease Start" in priority_missing or "Lease End" in priority_missing:
                print("   - Add date extraction patterns for lease dates")
            if "Move In Date" in priority_missing or "Move Out Date" in priority_missing:
                print("   - Add move date extraction from document context")
            if "Area / Square Ft" in priority_missing:
                print("   - Improve area/sqft extraction patterns")
            if "Tenant Name" in priority_missing:
                print("   - Enhance name extraction for all unit types")
        else:
            print("🎉 All fields are well captured!")
        
        return field_results

if __name__ == "__main__":
    audit_extracted_fields()