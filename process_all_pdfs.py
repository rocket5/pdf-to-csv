#!/usr/bin/env python3
import os
import glob
import subprocess
import argparse
from datetime import datetime

def process_all_pdfs(input_dir="in", output_dir="out", thorough=False, verbose=False):
    """Process all PDF files in the input directory and save CSV files to the output directory."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all PDF files in the input directory
    pdf_files = sorted(glob.glob(os.path.join(input_dir, "*.pdf")))
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir} directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process.")
    start_time = datetime.now()
    
    # Process each PDF file
    for i, pdf_file in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_file)
        print(f"[{i}/{len(pdf_files)}] Processing {filename}...")
        
        # Build command arguments
        cmd = ["python", "pdf_to_csv.py", pdf_file]
        if verbose:
            cmd.append("-v")
        if thorough:
            cmd.append("-t")
        
        # Run the pdf_to_csv.py script
        subprocess.run(cmd)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"\nCompleted processing {len(pdf_files)} PDF files in {duration:.2f} seconds.")

def main():
    parser = argparse.ArgumentParser(description='Process all PDF files in the input directory.')
    parser.add_argument('--input', '-i', default='in', help='Input directory containing PDF files')
    parser.add_argument('--output', '-o', default='out', help='Output directory for CSV files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--thorough', '-t', action='store_true', help='Enable thorough processing')
    
    args = parser.parse_args()
    
    process_all_pdfs(
        input_dir=args.input,
        output_dir=args.output,
        verbose=args.verbose,
        thorough=args.thorough
    )

if __name__ == "__main__":
    main() 