#!/usr/bin/env python3
import os
import pandas as pd
import glob
import re

def combine_csv_files():
    # Path to the output directory
    out_dir = 'out'
    # Output file path
    output_file = 'out/combined.csv'
    
    # Get all CSV files in the out directory
    csv_files = glob.glob(os.path.join(out_dir, '*.csv'))
    
    if not csv_files:
        print("No CSV files found in the 'out' directory.")
        return
    
    # Filter out the combined.csv file if it exists
    csv_files = [f for f in csv_files if os.path.basename(f) != 'combined.csv']
    
    # Sort files numerically by filename (01.csv, 02.csv, etc.)
    csv_files.sort(key=lambda f: int(re.search(r'(\d+)\.csv$', f).group(1)))
    
    print(f"Found {len(csv_files)} CSV files to process in order: {[os.path.basename(f) for f in csv_files]}")
    
    # List to store DataFrames
    dfs = []
    
    # Read each CSV file and append to the list
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            file_name = os.path.basename(csv_file)
            print(f"Reading: {file_name} - {len(df)} rows")
            # Add a column to track the source file
            df['source_file'] = file_name
            dfs.append(df)
        except Exception as e:
            print(f"Error reading {csv_file}: {str(e)}")
    
    if not dfs:
        print("No valid CSV files to combine.")
        return
    
    # Combine all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Convert transaction_date to datetime for proper sorting
    combined_df['transaction_date'] = pd.to_datetime(combined_df['transaction_date'])
    
    # Sort by transaction_date
    combined_df = combined_df.sort_values('transaction_date')
    
    # Convert back to string format
    combined_df['transaction_date'] = combined_df['transaction_date'].dt.strftime('%Y-%m-%d')
    
    # Remove the source_file column before saving
    combined_df = combined_df.drop('source_file', axis=1)
    
    # Write to output file
    combined_df.to_csv(output_file, index=False)
    
    print(f"Combined CSV created successfully: {output_file}")
    print(f"Total rows: {len(combined_df)}")

if __name__ == "__main__":
    combine_csv_files() 