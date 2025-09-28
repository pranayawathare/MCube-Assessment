"""
Simple test script to quickly identify parsing issues
Run this first to understand what's happening
"""

import sys
import os
from pathlib import Path

def quick_test():
    """Quick test of the debug tool."""
    print("=== QUICK PDF PARSING TEST ===")
    
    # Test files
    test_files = [
        "docs/machine_readable_financial_data.pdf",
        "docs/scanned_financial_data.pdf"
    ]
    
    for pdf_path in test_files:
        if not Path(pdf_path).exists():
            print(f"❌ File not found: {pdf_path}")
            continue
            
        print(f"\n📄 Testing: {pdf_path}")
        print("-" * 50)
        
        try:
            import fitz
            doc = fitz.open(pdf_path)
            page = doc[0]
            
            # Basic info
            print(f"Pages: {len(doc)}")
            print(f"Fonts: {len(page.get_fonts())}")
            print(f"Is scanned: {len(page.get_fonts()) == 0}")
            
            # Try different text extraction methods
            methods = {
                "text": lambda: page.get_text("text"),
                "blocks": lambda: "\n".join([block[4] for block in page.get_text("blocks") if len(block) > 4]),
                "words": lambda: " ".join([word[4] for word in page.get_text("words")])
            }
            
            best_text = ""
            best_method = ""
            
            for method_name, method_func in methods.items():
                try:
                    text = method_func()
                    print(f"{method_name.upper()}: {len(text)} chars")
                    
                    if len(text) > len(best_text):
                        best_text = text
                        best_method = method_name
                        
                except Exception as e:
                    print(f"{method_name.upper()}: ERROR - {e}")
            
            print(f"\nBest method: {best_method} ({len(best_text)} chars)")
            
            if best_text:
                # Quick pattern tests
                import re
                
                # Unit test
                unit_matches = re.findall(r'\b(?:01-|02-)?(\d{3})\b', best_text)
                print(f"Units found: {len(set(unit_matches))} unique")
                
                # Rent test
                rent_matches = re.findall(r'1[.,]?[0-9]{3}[.,]?00', best_text)
                print(f"Rent patterns: {len(rent_matches)} found")
                
                # Show sample
                lines = best_text.split('\n')
                non_empty_lines = [l.strip() for l in lines if l.strip()]
                print(f"Non-empty lines: {len(non_empty_lines)}")
                
                if non_empty_lines:
                    print("First few lines:")
                    for i, line in enumerate(non_empty_lines[:3]):
                        print(f"  {i+1}: {line[:80]}...")
            
            doc.close()
            
        except Exception as e:
            print(f"❌ Error processing {pdf_path}: {e}")

def main():
    """Main test function."""
    print("🔍 Running quick PDF parsing test...")
    print("This will help identify the core issues.")
    
    quick_test()
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("1. Run the comprehensive debug tool:")
    print("   python comprehensive_debug.py docs/machine_readable_financial_data.pdf")
    print("2. If text extraction is the issue, try the QuickFix parser")
    print("3. Look at the actual text being extracted")
    print("="*60)

if __name__ == "__main__":
    main()