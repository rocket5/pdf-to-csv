#!/usr/bin/env python3
from PyPDF2 import PdfReader
import sys

def extract_and_print_pdf_content(pdf_path):
    """Extract and print the content of a PDF file for debugging."""
    reader = PdfReader(pdf_path)
    
    print(f"PDF has {len(reader.pages)} pages")
    
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text()
        
        print(f"\n\n===== PAGE {page_num+1} =====\n")
        print(text)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_pdf.py <pdf_file>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    extract_and_print_pdf_content(pdf_path) 