"""
Comprehensive PDF diagnostic to find where the actual data is located
"""

import fitz
import re
import os
from pathlib import Path

def comprehensive_pdf_diagnosis(pdf_path: str):
    """Complete diagnosis of PDF structure and content."""
    
    print(f"🔍 COMPREHENSIVE PDF DIAGNOSIS")
    print(f"File: {pdf_path}")
    print("="*60)
    
    if not Path(pdf_path).exists():
        print(f"❌ File not found!")
        return
    
    doc = fitz.open(pdf_path)
    
    print(f"📄 PDF STRUCTURE:")
    print(f"  Total pages: {len(doc)}")
    print(f"  Metadata: {doc.metadata}")
    print(f"  Is encrypted: {doc.is_encrypted}")
    print(f"  Page count: {doc.page_count}")
    
    # Check each page thoroughly
    for page_num, page in enumerate(doc):
        print(f"\n{'='*40}")
        print(f"PAGE {page_num + 1} ANALYSIS")
        print(f"{'='*40}")
        
        # Basic page info
        print(f"📐 Page dimensions: {page.rect}")
        print(f"🔄 Rotation: {page.rotation}")
        
        # Font analysis
        fonts = page.get_fonts()
        print(f"🔤 Fonts found: {len(fonts)}")
        if fonts:
            for i, font in enumerate(fonts[:3]):
                print(f"  Font {i+1}: {font}")
        
        # Image analysis
        images = page.get_images()
        print(f"🖼️  Images: {len(images)}")
        
        # Test ALL extraction methods
        extraction_results = {}
        
        # Method 1: Basic text
        try:
            text1 = page.get_text("text")
            extraction_results["text"] = text1
            print(f"📝 Text extraction: {len(text1)} chars")
        except Exception as e:
            print(f"📝 Text extraction: FAILED - {e}")
        
        # Method 2: Blocks
        try:
            blocks = page.get_text("blocks")
            text2 = "\n".join([block[4] for block in blocks if len(block) > 4])
            extraction_results["blocks"] = text2
            print(f"🧱 Blocks extraction: {len(blocks)} blocks, {len(text2)} chars")
        except Exception as e:
            print(f"🧱 Blocks extraction: FAILED - {e}")
        
        # Method 3: Words
        try:
            words = page.get_text("words")
            text3 = " ".join([word[4] for word in words])
            extraction_results["words"] = text3
            print(f"📖 Words extraction: {len(words)} words, {len(text3)} chars")
            
            # Show first 10 words with positions
            if words:
                print(f"  First 10 words:")
                for i, word in enumerate(words[:10]):
                    x0, y0, x1, y1, text, *_ = word
                    print(f"    {i+1}: '{text}' at ({x0:.1f}, {y0:.1f})")
        except Exception as e:
            print(f"📖 Words extraction: FAILED - {e}")
        
        # Method 4: Dict
        try:
            dict_result = page.get_text("dict")
            if dict_result and 'blocks' in dict_result:
                dict_text = ""
                for block in dict_result['blocks']:
                    if 'lines' in block:
                        for line in block['lines']:
                            for span in line.get('spans', []):
                                dict_text += span.get('text', '') + " "
                            dict_text += "\n"
                extraction_results["dict"] = dict_text
                print(f"📚 Dict extraction: {len(dict_text)} chars")
        except Exception as e:
            print(f"📚 Dict extraction: FAILED - {e}")
        
        # Method 5: Raw dict
        try:
            raw_dict = page.get_text("rawdict")
            if raw_dict and 'blocks' in raw_dict:
                raw_text = ""
                for block in raw_dict['blocks']:
                    if 'lines' in block:
                        for line in block['lines']:
                            for span in line.get('spans', []):
                                raw_text += span.get('text', '') + " "
                            raw_text += "\n"
                extraction_results["rawdict"] = raw_text
                print(f"🔧 Raw dict extraction: {len(raw_text)} chars")
        except Exception as e:
            print(f"🔧 Raw dict extraction: FAILED - {e}")
        
        # Method 6: HTML
        try:
            html = page.get_text("html")
            # Extract text from HTML
            import re
            html_text = re.sub(r'<[^>]+>', ' ', html)
            html_text = re.sub(r'\s+', ' ', html_text).strip()
            extraction_results["html"] = html_text
            print(f"🌐 HTML extraction: {len(html_text)} chars")
        except Exception as e:
            print(f"🌐 HTML extraction: FAILED - {e}")
        
        # Method 7: XHTML
        try:
            xhtml = page.get_text("xhtml")
            xhtml_text = re.sub(r'<[^>]+>', ' ', xhtml)
            xhtml_text = re.sub(r'\s+', ' ', xhtml_text).strip()
            extraction_results["xhtml"] = xhtml_text
            print(f"📰 XHTML extraction: {len(xhtml_text)} chars")
        except Exception as e:
            print(f"📰 XHTML extraction: FAILED - {e}")
        
        # Method 8: Try table extraction if available
        try:
            if hasattr(page, 'find_tables'):
                tables = page.find_tables()
                print(f"📊 Table detection: {len(tables)} tables found")
                if tables:
                    table_text = ""
                    for i, table in enumerate(tables):
                        print(f"  Table {i+1}: {table.row_count} rows x {table.col_count} cols")
                        try:
                            df = table.to_pandas()
                            for _, row in df.iterrows():
                                row_text = "\t".join([str(cell) for cell in row if str(cell) != 'nan'])
                                table_text += row_text + "\n"
                        except Exception as e:
                            print(f"    Table extraction failed: {e}")
                    extraction_results["table"] = table_text
                    print(f"  Combined table text: {len(table_text)} chars")
            else:
                print(f"📊 Table detection: Not available in this PyMuPDF version")
        except Exception as e:
            print(f"📊 Table detection: FAILED - {e}")
        
        # Find the best extraction method for this page
        best_method = ""
        best_text = ""
        best_length = 0
        
        for method, text in extraction_results.items():
            if len(text) > best_length:
                best_length = len(text)
                best_text = text
                best_method = method
        
        print(f"\n🏆 BEST METHOD FOR PAGE {page_num + 1}: {best_method} ({best_length} chars)")
        
        # Test for unit patterns in best text
        if best_text and len(best_text) > 50:
            # Look for expected units
            expected_units = list(range(101, 129)) + list(range(201, 228))
            unit_pattern = r'\b(1[0-2][0-8]|20[0-7]|21[0-9]|22[0-7])\b'
            
            found_units = set()
            for match in re.finditer(unit_pattern, best_text):
                unit_num = int(match.group(1))
                if unit_num in expected_units:
                    found_units.add(unit_num)
            
            print(f"🎯 UNITS FOUND: {len(found_units)}/55 ({len(found_units)/55*100:.1f}%)")
            if found_units:
                sample_units = sorted(list(found_units))[:20]
                print(f"   Sample units: {sample_units}")
            
            # Look for other patterns
            rent_patterns = len(re.findall(r'\b[1-5]\d{3}\b', best_text))
            status_patterns = len(re.findall(r'\b(occupied|vacant)\b', best_text, re.IGNORECASE))
            money_patterns = len(re.findall(r'\$\d+', best_text))
            
            print(f"🔍 OTHER PATTERNS:")
            print(f"   Rent-like numbers: {rent_patterns}")
            print(f"   Status words: {status_patterns}")
            print(f"   Dollar signs: {money_patterns}")
            
            # Show sample text
            print(f"\n📄 SAMPLE TEXT (first 300 chars):")
            print(f"   {repr(best_text[:300])}")
            
            # Show first few lines
            lines = best_text.split('\n')
            non_empty_lines = [l.strip() for l in lines if l.strip()]
            print(f"\n📋 FIRST 10 NON-EMPTY LINES:")
            for i, line in enumerate(non_empty_lines[:10]):
                print(f"   {i+1}: {repr(line[:80])}")
        
        else:
            print(f"❌ NO MEANINGFUL TEXT FOUND ON PAGE {page_num + 1}")
            
            # If no text found, check if this might be an image-based page
            print(f"🔍 CHECKING IF PAGE IS IMAGE-BASED...")
            try:
                # Convert to image and try OCR
                zoom = 2.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                print(f"   Page rendered as image: {pix.width}x{pix.height} pixels")
                
                # Try OCR if available
                try:
                    import easyocr
                    reader = easyocr.Reader(['en'], gpu=False)
                    
                    from PIL import Image
                    import numpy as np
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img_array = np.array(img)
                    
                    ocr_results = reader.readtext(img_array, detail=1)
                    ocr_text = " ".join([r[1] for r in ocr_results])
                    
                    print(f"   OCR extracted: {len(ocr_text)} chars")
                    if ocr_text:
                        print(f"   OCR sample: {repr(ocr_text[:200])}")
                        
                        # Test OCR for units
                        ocr_units = set()
                        for match in re.finditer(unit_pattern, ocr_text):
                            unit_num = int(match.group(1))
                            if unit_num in expected_units:
                                ocr_units.add(unit_num)
                        
                        if ocr_units:
                            print(f"   🎯 OCR found {len(ocr_units)} units!")
                
                except ImportError:
                    print(f"   OCR not available (easyocr not installed)")
                except Exception as e:
                    print(f"   OCR failed: {e}")
                    
            except Exception as e:
                print(f"   Image conversion failed: {e}")
    
    doc.close()
    
    # Summary and recommendations
    print(f"\n{'='*60}")
    print(f"DIAGNOSIS SUMMARY & RECOMMENDATIONS")
    print(f"{'='*60}")
    print(f"1. Check which page(s) have the most content")
    print(f"2. Use the extraction method that gives the most text")
    print(f"3. If no page has good text extraction, the PDF might be:")
    print(f"   - Image-based (need OCR)")
    print(f"   - Protected/encrypted")
    print(f"   - Using non-standard encoding")
    print(f"4. Expected: 55 units (101-128, 201-227)")

def main():
    """Run comprehensive diagnosis."""
    pdf_path = "docs/machine_readable_financial_data.pdf"
    
    if len(os.sys.argv) > 1:
        pdf_path = os.sys.argv[1]
    
    comprehensive_pdf_diagnosis(pdf_path)

if __name__ == "__main__":
    main()