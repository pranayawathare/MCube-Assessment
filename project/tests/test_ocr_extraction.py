"""
Test script to verify OCR extraction works for machine-readable PDF
Run this before updating your document_parser.py
"""

import fitz
import re
import easyocr
from PIL import Image
import numpy as np

def test_ocr_extraction():
    """Test OCR extraction on the machine-readable PDF."""
    
    pdf_path = "docs/machine_readable_financial_data.pdf"
    
    print(f"🔍 TESTING OCR EXTRACTION")
    print(f"File: {pdf_path}")
    print("="*50)
    
    # Expected units
    expected_units = list(range(101, 129)) + list(range(201, 228))  # 55 total
    print(f"Expected: {len(expected_units)} units (101-128, 201-227)")
    
    # Initialize OCR
    print(f"🔧 Initializing OCR...")
    reader = easyocr.Reader(['en'], gpu=False)
    
    # Open PDF
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    # Convert to image for OCR
    print(f"🖼️  Converting PDF to image...")
    zoom = 2.0  # Higher resolution
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_array = np.array(img)
    
    print(f"Image size: {img.size}")
    
    # Run OCR
    print(f"🔍 Running OCR...")
    ocr_results = reader.readtext(img_array, detail=1)
    ocr_text = " ".join([r[1] for r in ocr_results])
    
    print(f"OCR extracted: {len(ocr_text)} characters")
    print(f"OCR confidence: {len(ocr_results)} text blocks detected")
    
    # Clean OCR text
    cleaned_text = re.sub(r'[^\w\s\$\.,\-/]', ' ', ocr_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    print(f"Cleaned text: {len(cleaned_text)} characters")
    
    # Look for units
    print(f"\n🎯 SEARCHING FOR UNITS...")
    
    unit_patterns = [
        (r'\b(1[0-2][0-8])\b', "Units 101-128"),
        (r'\b(20[0-7]|21[0-9]|22[0-7])\b', "Units 201-227"),
        (r'\b([12]\d{2})\b', "Any 3-digit 1XX/2XX"),
    ]
    
    all_found_units = set()
    
    for pattern, description in unit_patterns:
        matches = re.findall(pattern, cleaned_text)
        valid_units = set()
        
        for match in matches:
            try:
                unit_num = int(match)
                if unit_num in expected_units:
                    valid_units.add(unit_num)
                    all_found_units.add(unit_num)
            except ValueError:
                continue
        
        print(f"  {description}: {len(valid_units)} units found")
        if valid_units:
            sample = sorted(list(valid_units))[:10]
            print(f"    Sample: {sample}")
    
    # Summary
    found_100s = [u for u in all_found_units if 101 <= u <= 128]
    found_200s = [u for u in all_found_units if 201 <= u <= 227]
    
    print(f"\n📊 EXTRACTION RESULTS:")
    print(f"  Units 101-128: {len(found_100s)}/28 ({len(found_100s)/28*100:.1f}%)")
    print(f"  Units 201-227: {len(found_200s)}/27 ({len(found_200s)/27*100:.1f}%)")
    print(f"  Total found: {len(all_found_units)}/55 ({len(all_found_units)/55*100:.1f}%)")
    
    # Check for other data patterns
    print(f"\n🔍 OTHER PATTERNS:")
    rent_patterns = len(re.findall(r'\b[1-5]\d{3}\b', cleaned_text))
    status_patterns = len(re.findall(r'\b(occupied|vacant|occ|vac)\b', cleaned_text, re.IGNORECASE))
    money_patterns = len(re.findall(r'\$\d+', cleaned_text))
    
    print(f"  Rent-like numbers: {rent_patterns}")
    print(f"  Status words: {status_patterns}")
    print(f"  Dollar signs: {money_patterns}")
    
    # Show sample OCR text
    print(f"\n📄 SAMPLE OCR TEXT (first 500 chars):")
    print(f"   {repr(cleaned_text[:500])}")
    
    # Show first few lines
    lines = cleaned_text.split()  # Split by whitespace since OCR doesn't preserve line breaks well
    print(f"\n📋 FIRST 20 OCR TOKENS:")
    for i, token in enumerate(lines[:20]):
        if len(token) > 2:  # Skip very short tokens
            print(f"   {i+1}: {repr(token)}")
    
    # Assessment
    success_rate = len(all_found_units) / 55 * 100
    
    print(f"\n🏆 ASSESSMENT:")
    if success_rate >= 80:
        print(f"✅ EXCELLENT: {success_rate:.1f}% extraction rate")
        print(f"   Ready to integrate OCR fallback into parser!")
    elif success_rate >= 50:
        print(f"✅ GOOD: {success_rate:.1f}% extraction rate")
        print(f"   OCR approach will work, may need minor tuning")
    elif success_rate >= 20:
        print(f"⚠️  MODERATE: {success_rate:.1f}% extraction rate")
        print(f"   OCR finds some units, needs pattern improvements")
    else:
        print(f"❌ LOW: {success_rate:.1f}% extraction rate")
        print(f"   OCR approach needs significant work")
    
    doc.close()
    
    return len(all_found_units), expected_units

if __name__ == "__main__":
    test_ocr_extraction()