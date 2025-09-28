#!/usr/bin/env python3
"""
Nuclear Reset Script - Complete Database and Vector Store Cleanup
Removes all stored data to fix duplicate unit issues and start fresh.
"""

import os
import shutil
import sqlite3
import glob
from pathlib import Path

def nuclear_reset():
    """Completely reset all stored data - database, vectors, and cache."""
    
    print("🚨 NUCLEAR RESET INITIATED 🚨")
    print("=" * 50)
    
    reset_count = 0
    
    # 1. Remove SQLite database
    db_files = [
        "data/documents.db",
        "data/documents.db-journal",
        "data/documents.db-wal",
        "data/documents.db-shm"
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                print(f"✅ Deleted: {db_file}")
                reset_count += 1
            except Exception as e:
                print(f"❌ Failed to delete {db_file}: {e}")
    
    # 2. Remove vector storage directory
    vector_dirs = [
        "data/vectors",
        "data/qdrant_storage",
        "data/embeddings"
    ]
    
    for vector_dir in vector_dirs:
        if os.path.exists(vector_dir):
            try:
                shutil.rmtree(vector_dir)
                print(f"✅ Deleted directory: {vector_dir}")
                reset_count += 1
            except Exception as e:
                print(f"❌ Failed to delete {vector_dir}: {e}")
    
    # 3. Remove any pickle files (cached embeddings)
    pickle_pattern = "data/*.pkl"
    pickle_files = glob.glob(pickle_pattern)
    
    for pickle_file in pickle_files:
        try:
            os.remove(pickle_file)
            print(f"✅ Deleted cache: {pickle_file}")
            reset_count += 1
        except Exception as e:
            print(f"❌ Failed to delete {pickle_file}: {e}")
    
    # 4. Remove any JSON metadata files
    json_pattern = "data/*.json"
    json_files = glob.glob(json_pattern)
    
    for json_file in json_files:
        try:
            os.remove(json_file)
            print(f"✅ Deleted metadata: {json_file}")
            reset_count += 1
        except Exception as e:
            print(f"❌ Failed to delete {json_file}: {e}")
    
    # 5. Remove any temporary files
    temp_patterns = [
        "data/*.tmp",
        "data/*.temp",
        "data/*.log",
        "*.tmp",
        "*.temp"
    ]
    
    for pattern in temp_patterns:
        temp_files = glob.glob(pattern)
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
                print(f"✅ Deleted temp: {temp_file}")
                reset_count += 1
            except Exception as e:
                print(f"❌ Failed to delete {temp_file}: {e}")
    
    # 6. Recreate clean data directory structure
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir(exist_ok=True)
        print(f"✅ Recreated: {data_dir}")
    
    # 7. Verify cleanup by checking for any remaining files
    remaining_files = []
    if data_dir.exists():
        for item in data_dir.rglob("*"):
            if item.is_file():
                remaining_files.append(str(item))
    
    print("\n" + "=" * 50)
    print("🧹 NUCLEAR RESET COMPLETE")
    print("=" * 50)
    print(f"📊 Files/Directories Removed: {reset_count}")
    
    if remaining_files:
        print(f"⚠️  Remaining files in data/: {len(remaining_files)}")
        for remaining in remaining_files[:5]:  # Show first 5
            print(f"   - {remaining}")
        if len(remaining_files) > 5:
            print(f"   ... and {len(remaining_files) - 5} more")
    else:
        print("✅ All data files successfully removed")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run: python main.py --process docs/machine_readable_financial_data.pdf docs/scanned_financial_data.pdf")
    print("2. Run: python data_field_audit.py")
    print("3. Run: python main.py --interactive")
    print("\n📈 Expected Result: 73 total units (55 + 18)")
    print("=" * 50)

def confirm_reset():
    """Ask for confirmation before nuclear reset."""
    print("⚠️  NUCLEAR RESET WARNING ⚠️")
    print("This will permanently delete:")
    print("• All processed documents from database")
    print("• All vector embeddings and search indices") 
    print("• All cached data and temporary files")
    print("• You will need to reprocess all documents")
    
    confirmation = input("\nType 'RESET' to confirm nuclear reset: ").strip()
    
    if confirmation == "RESET":
        return True
    else:
        print("❌ Nuclear reset cancelled.")
        return False

if __name__ == "__main__":
    print("🚀 Nuclear Reset Script for MCube Assessment")
    print("Fixes duplicate unit counting (146 → 73 units)")
    print()
    
    if confirm_reset():
        nuclear_reset()
    else:
        print("\n💡 TIP: You can also manually delete the 'data/' folder")
        print("   and rerun document processing to fix the duplicate issue.")