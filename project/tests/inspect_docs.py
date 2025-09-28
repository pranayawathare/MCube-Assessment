"""
Script to manually inspect what's being extracted from the documents
"""

import sys
import os
import fitz
import re

def inspect_document(pdf_path):
    """Manually inspect document content"""
    print(f"\n{'='*80}")
    print(f"INSPECTING: {pdf_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return
    
    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        
        print(f"\nPage {page_num + 1}:")
        print(f"Total characters: {len(text)}")
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        print(f"Non-empty lines: {len(lines)}")
        
        # Show first 30 lines
        print(f"\nFirst 30 lines:")
        for i, line in enumerate(lines[:30]):
            print(f"{i+1:3d}: {line}")
        
        # Look for patterns
        print(f"\nPATTERN ANALYSIS:")
        
        # Unit numbers
        unit_pattern = r'\b(\d{2}-\d{3})\b'
        units = re.findall(unit_pattern, text)
        print(f"Unit numbers found: {len(units)} - {units[:10]}")
        
        # Rent patterns
        rent_patterns = [
            r'(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)\s+rent',
            r'\$(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)',
            r'Total\s+(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        all_rents = []
        for pattern in rent_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            all_rents.extend(matches)
        print(f"Rent amounts found: {len(all_rents)} - {all_rents[:10]}")
        
        # Occupancy status
        occupancy = re.findall(r'\b(Occupied|Vacant)\b', text, re.IGNORECASE)
        print(f"Occupancy status found: {len(occupancy)} - {occupancy[:10]}")
        
        # Tenant patterns
        tenant_ids = re.findall(r't(\d{7,8})', text)
        print(f"Tenant IDs found: {len(tenant_ids)} - {tenant_ids[:10]}")
        
        # Names (potential tenants)
        names = re.findall(r'\b([A-Z][a-z]+,\s*[A-Z][a-z]+)\b', text)
        print(f"Name patterns found: {len(names)} - {names[:10]}")
        
        # Areas
        areas = re.findall(r'\b(\d{3,4})\s+(?:Occupied|Vacant|sq)', text, re.IGNORECASE)
        print(f"Area patterns found: {len(areas)} - {areas[:10]}")
        
        # Sample lines with units
        print(f"\nSAMPLE LINES WITH UNIT NUMBERS:")
        for i, line in enumerate(lines):
            if re.search(unit_pattern, line):
                print(f"{i+1:3d}: {line}")
                if i > 10:  # Show first 10 unit lines
                    break
    
    doc.close()

def main():
    files = [
        "docs/machine_readable_financial_data.pdf",
        "docs/scanned_financial_data.pdf"
    ]
    
    for file_path in files:
        inspect_document(file_path)

if __name__ == "__main__":
    main()