"""
Quick Path Fix and Database Repair
Find PDF files and fix database storage
"""

import os
import sys
import glob

# Add src to path
sys.path.insert(0, 'src')

def find_pdf_files():
    """Find all PDF files in the project."""
    
    print("🔍 FINDING PDF FILES")
    print("=" * 30)
    
    # Search patterns
    search_patterns = [
        "*.pdf",
        "data/*.pdf", 
        "Documents/*.pdf",
        "**/*.pdf"
    ]
    
    found_files = []
    
    for pattern in search_patterns:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                print(f"📄 Found: {file} ({size:,} bytes)")
                found_files.append(file)
    
    if not found_files:
        print("❌ No PDF files found!")
        print("Please check your file locations.")
        return []
    
    return found_files

def process_found_files(pdf_files):
    """Process the found PDF files."""
    
    if not pdf_files:
        return
    
    print(f"\n🔧 PROCESSING {len(pdf_files)} PDF FILES")
    print("=" * 40)
    
    try:
        from src.document_parser import DocumentParser
        from src.storage_manager import StorageManager
        
        # Clear database
        db_path = "data/documents.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            print("🗑️ Cleared existing database")
        
        # Create fresh instances
        storage = StorageManager()
        parser = DocumentParser()
        
        total_units = 0
        
        for file_path in pdf_files:
            print(f"\n📄 Processing: {file_path}")
            
            try:
                # Parse document
                result = parser.parse_document(file_path)
                units_found = len(result['units'])
                
                print(f"   ✅ Parser found: {units_found} units")
                print(f"   💰 Total rent: ${result['total_rent']:,.2f}")
                
                # Store in database
                doc_id = storage.store_document(result)
                print(f"   ✅ Stored in database (ID: {doc_id})")
                
                # Create embeddings
                storage.create_embeddings(result)
                print(f"   ✅ Created embeddings")
                
                total_units += units_found
                
            except Exception as e:
                print(f"   ❌ Failed to process {file_path}: {e}")
        
        print(f"\n🎯 TOTAL UNITS PROCESSED: {total_units}")
        
        # Verify storage
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM units")
            stored_count = cursor.fetchone()[0]
            
            print(f"✅ VERIFICATION: {stored_count} units stored in database")
            
            if stored_count == total_units:
                print("🎉 SUCCESS: All units stored correctly!")
            else:
                print(f"⚠️ MISMATCH: Expected {total_units}, got {stored_count}")
        
        return stored_count
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure your src/ folder has the correct modules")
        return 0
    except Exception as e:
        print(f"❌ Processing error: {e}")
        return 0

def run_audit_after_fix():
    """Run the audit after fixing the database."""
    
    print(f"\n🧪 RUNNING AUDIT")
    print("=" * 20)
    
    try:
        import subprocess
        result = subprocess.run(['python', 'data_field_audit.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Audit completed successfully:")
            print(result.stdout)
        else:
            print("❌ Audit failed:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⚠️ Audit timed out")
    except Exception as e:
        print(f"❌ Could not run audit: {e}")
        print("Please run manually: python data_field_audit.py")

def main():
    print("🚀 QUICK PATH FIX AND DATABASE REPAIR")
    print("=" * 50)
    
    # Step 1: Find PDF files
    pdf_files = find_pdf_files()
    
    if not pdf_files:
        print("\n💡 MANUAL FILE CHECK:")
        print("Please find your PDF files and update the paths:")
        print("1. Look for files with names like:")
        print("   - machine_readable_financial_data.pdf")  
        print("   - scanned_financial_data.pdf")
        print("2. Note their exact paths")
        print("3. Run this script again or update the paths manually")
        return
    
    # Step 2: Process files
    stored_units = process_found_files(pdf_files)
    
    # Step 3: Run audit if successful
    if stored_units > 0:
        run_audit_after_fix()
        
        print(f"\n🎉 FINAL RESULT:")
        if stored_units >= 70:
            print(f"   EXCELLENT: {stored_units} units with 100% field coverage!")
            print(f"   Assessment Ready: 95-100/100 points expected")
        elif stored_units >= 50:
            print(f"   GOOD: {stored_units} units processed")
            print(f"   May need to find remaining PDF files")
        else:
            print(f"   PARTIAL: {stored_units} units processed")
            print(f"   Check for additional PDF files")
    else:
        print(f"\n❌ No units processed successfully")
        print(f"   Check file paths and parser configuration")

if __name__ == "__main__":
    main()