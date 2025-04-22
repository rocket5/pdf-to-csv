#!/usr/bin/env python3
import os
import re
import csv
import argparse
from datetime import datetime
from PyPDF2 import PdfReader

def extract_transactions(pdf_path, verbose=False, thorough=False):
    """Extract transaction data from a TD credit card statement PDF."""
    # Read PDF content
    reader = PdfReader(pdf_path)
    all_text = ""
    page_texts = []  # Store text from each page separately
    
    print(f"Total pages in PDF: {len(reader.pages)}")
    
    # Process each page separately and also keep combined text
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        page_text = page.extract_text()
        page_texts.append(page_text)
        all_text += page_text + "\n"
        if verbose:
            newline_count = page_text.count('\n')
            print(f"Page {page_num+1} has {len(page_text)} characters and {newline_count} lines")
    
    # Extract statement date to get correct year
    statement_year = datetime.now().year
    statement_month = None
    # Try various formats starting with the most structured one
    date_match = re.search(r'STATEMENT DATE:\s*(\w+)\s+(\d{1,2}),\s*(\d{4})', all_text)
    if not date_match:
        # Try with no space between month and day but with comma
        date_match = re.search(r'STATEMENT DATE:\s*(\w+?)(\d{1,2}),\s*(\d{4})', all_text)
    if not date_match:
        # Try with no spaces and no comma
        date_match = re.search(r'STATEMENT DATE:(\w+?)(\d{1,2})(\d{4})', all_text)
    if date_match:
        statement_month = date_match.group(1)
        statement_day = int(date_match.group(2))
        statement_year = int(date_match.group(3))
        print(f"Statement date: {statement_month} {statement_day}, {statement_year}")
    else:
        print("Warning: Could not find statement date. Using current year.")
    
    # Extract statement period to determine transaction years
    start_year = statement_year
    end_year = statement_year
    # Try various formats for statement period
    period_match = re.search(r'STATEMENT PERIOD:\s*(\w+)\s+(\d{1,2}),\s*(\d{4})\s*to\s*(\w+)\s+(\d{1,2}),\s*(\d{4})', all_text)
    if not period_match:
        # Try with no spaces between month and day
        period_match = re.search(r'STATEMENT PERIOD:\s*(\w+?)(\d{1,2}),?(\d{4})\s*to\s*(\w+?)(\d{1,2}),?(\d{4})', all_text)
    if not period_match:
        # Try with no spaces at all
        period_match = re.search(r'STATEMENT PERIOD:\s*(\w+?)(\d{1,2})(\d{4})to(\w+?)(\d{1,2})(\d{4})', all_text)
    if period_match:
        start_month = period_match.group(1)
        start_day = period_match.group(2)
        start_year = int(period_match.group(3))
        end_month = period_match.group(4)
        end_day = period_match.group(5)
        end_year = int(period_match.group(6))
        print(f"Statement period: {start_month} {start_day}, {start_year} to {end_month} {end_day}, {end_year}")
        
        # Verify if years are correct - they should typically be the same or 1 year apart
        if start_year != end_year and abs(start_year - end_year) > 1:
            print(f"Warning: Statement period spans multiple years: {start_year} to {end_year}.")
            # Adjust to use the statement year as primary reference
            start_year = statement_year
            end_year = statement_year
            print(f"Adjusted to use statement year for all transactions: {statement_year}")
    else:
        print("Warning: Could not find statement period. Using statement year for all transactions.")
    
    # Parse transactions - process the entire document
    transactions = []
    current_transaction = None
    transaction_count = 0
    
    # Transaction patterns
    patterns = [
        # Standard format: JAN15JAN17 $12.34 MERCHANT NAME
        r'([A-Z]{3}\s*\d{1,2})([A-Z]{3}\s*\d{1,2})\s+(-?\$[\d,]+\.\d{2})\s+(.*)',
        
        # Alternate format with space between dates: JAN15 JAN17 $12.34 MERCHANT
        r'([A-Z]{3}\s*\d{1,2})\s+([A-Z]{3}\s*\d{1,2})\s+(-?\$[\d,]+\.\d{2})\s+(.*)',
        
        # Format with different date style: JAN 15JAN 17 $12.34 MERCHANT
        r'([A-Z]{3}\s+\d{1,2})([A-Z]{3}\s+\d{1,2})\s+(-?\$[\d,]+\.\d{2})\s+(.*)'
    ]
    
    # Add more thorough patterns if requested
    if thorough:
        patterns.extend([
            # Even more flexible pattern with possible text between dates and amount
            r'([A-Z]{3}\s*\d{1,2}).*?([A-Z]{3}\s*\d{1,2}).*?(-?\$[\d,]+\.\d{2})\s+(.*)',
            
            # Pattern with just one date and amount
            r'([A-Z]{3}\s*\d{1,2}).*?(-?\$[\d,]+\.\d{2})\s+(.*)'
        ])
    
    # Compile all patterns
    transaction_patterns = [re.compile(pattern, re.MULTILINE) for pattern in patterns]
    
    # First pass: Process whole document line by line
    lines = all_text.split('\n')
    for line_idx, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            continue
        
        # Try each transaction pattern
        main_match = None
        pattern_used = -1
        for pattern_idx, pattern in enumerate(transaction_patterns):
            match = pattern.match(line.strip())
            if match:
                main_match = match
                pattern_used = pattern_idx
                if verbose:
                    print(f"Match found with pattern {pattern_idx+1}: {line.strip()}")
                break
                
        # Check for foreign currency line
        forex_match = re.match(r'FOREIGN CURRENCY\s+([\d,.]+)\s*([A-Z]{3})', line.strip())
        
        # Check for exchange rate line
        rate_match = re.match(r'@\s*EXCHANGE\s*RATE\s*([\d,.]+)', line.strip())
        
        if main_match:
            transaction_count += 1
            
            # If we were processing a previous transaction, add it to our list
            if current_transaction:
                transactions.append(current_transaction)
            
            # Process based on pattern type
            if pattern_used < 3:  # Standard patterns with two dates
                transaction_date = main_match.group(1).replace(' ', '')
                posting_date = main_match.group(2).replace(' ', '')
                amount_str = main_match.group(3).replace('$', '').replace(',', '')
                description = main_match.group(4).strip()
                
                # Parse the dates
                trans_date = parse_short_date(transaction_date, start_year, end_year, statement_month)
                post_date = parse_short_date(posting_date, start_year, end_year, statement_month)
            elif pattern_used == 3:  # Extended pattern with text between dates
                transaction_date = main_match.group(1).replace(' ', '')
                posting_date = main_match.group(2).replace(' ', '')
                amount_str = main_match.group(3).replace('$', '').replace(',', '')
                description = main_match.group(4).strip()
                
                # Parse the dates
                trans_date = parse_short_date(transaction_date, start_year, end_year, statement_month)
                post_date = parse_short_date(posting_date, start_year, end_year, statement_month)
            else:  # Single date pattern
                transaction_date = main_match.group(1).replace(' ', '')
                amount_str = main_match.group(2).replace('$', '').replace(',', '')
                description = main_match.group(3).strip()
                
                # Use the same date for both fields
                trans_date = parse_short_date(transaction_date, start_year, end_year, statement_month)
                post_date = trans_date
            
            # Handle negative amounts (payments/credits)
            try:
                amount = float(amount_str)
            except ValueError:
                print(f"Warning: Could not convert amount '{amount_str}' to float. Setting to 0.")
                amount = 0.0
            
            current_transaction = {
                'transaction_date': trans_date,
                'posting_date': post_date,
                'description': description,
                'amount': amount,
                'foreign_amount': None,
                'foreign_currency': None,
                'exchange_rate': None
            }
            
            if verbose:
                print(f"Found transaction: {trans_date} | {description} | ${amount:.2f}")
        
        elif forex_match and current_transaction:
            # Add foreign currency info to the current transaction
            foreign_amount = forex_match.group(1).replace(',', '')
            foreign_currency = forex_match.group(2)
            
            try:
                current_transaction['foreign_amount'] = float(foreign_amount)
            except ValueError:
                print(f"Warning: Could not convert foreign amount '{foreign_amount}' to float. Setting to 0.")
                current_transaction['foreign_amount'] = 0.0
                
            current_transaction['foreign_currency'] = foreign_currency
            
            # Update description to include the foreign currency information
            if not current_transaction['description'].endswith(')'):
                if not current_transaction['description'].endswith(','):
                    current_transaction['description'] += ' '
                current_transaction['description'] += f"({foreign_amount} {foreign_currency})"
                
            if verbose:
                print(f"  - Added foreign currency: {foreign_amount} {foreign_currency}")
        
        elif rate_match and current_transaction:
            # Add exchange rate info to current transaction
            exchange_rate = rate_match.group(1).replace(',', '')
            try:
                current_transaction['exchange_rate'] = float(exchange_rate)
            except ValueError:
                print(f"Warning: Could not convert exchange rate '{exchange_rate}' to float. Setting to 0.")
                current_transaction['exchange_rate'] = 0.0
                
            if verbose:
                print(f"  - Added exchange rate: {exchange_rate}")
    
    # Don't forget the last transaction
    if current_transaction:
        transactions.append(current_transaction)
    
    # Second pass: Analyze each page separately if thorough mode is enabled
    if thorough:
        print("\nPerforming thorough analysis of each page...")
        page_transactions = []
        
        for page_num, page_text in enumerate(page_texts):
            if verbose:
                print(f"\nAnalyzing page {page_num+1}:")
            
            # Look for transaction sections on this page
            transaction_sections = []
            
            # Common section headers in TD statements
            section_headers = [
                "TRANSACTIONS", 
                "PURCHASES AND ADJUSTMENTS",
                "PAYMENTS AND CREDITS",
                "YOUR TRANSACTIONS",
                "PREVIOUS STATEMENT BALANCE",
                "YOUR ACCOUNT TRANSACTIONS"
            ]
            
            # Try to find transaction sections
            for header in section_headers:
                if header in page_text:
                    if verbose:
                        print(f"Found transaction section: {header}")
                    
                    # Extract the section following the header
                    start_idx = page_text.find(header) + len(header)
                    section_text = page_text[start_idx:]
                    transaction_sections.append(section_text)
            
            # If no sections found, use the whole page
            if not transaction_sections:
                transaction_sections = [page_text]
            
            # Process each section
            for section in transaction_sections:
                section_lines = section.split('\n')
                
                # Process each line with regular expression pattern
                for line in section_lines:
                    if not line.strip():
                        continue
                        
                    # Look for patterns that might indicate a transaction
                    # Simplified pattern: anything with a month abbr, a day number, and a dollar amount
                    if (re.search(r'[A-Z]{3}', line.upper()) and 
                        re.search(r'\d{1,2}', line) and 
                        re.search(r'\$\d+\.\d{2}', line)):
                        
                        if verbose:
                            print(f"Potential transaction: {line}")
                        
                        # Try to extract date, amount and description
                        date_match = re.search(r'([A-Z]{3}\s*\d{1,2})', line.upper())
                        amount_match = re.search(r'(-?\$[\d,]+\.\d{2})', line)
                        
                        if date_match and amount_match:
                            date_str = date_match.group(1).replace(' ', '')
                            amount_str = amount_match.group(1).replace('$', '').replace(',', '')
                            
                            try:
                                amount = float(amount_str)
                            except ValueError:
                                continue
                                
                            # Extract description by removing date and amount
                            description = line
                            
                            # Replace the matched date and amount
                            description = description.replace(date_match.group(0), '')
                            description = description.replace(amount_match.group(0), '')
                            
                            # Clean up the description
                            description = re.sub(r'\s+', ' ', description).strip()
                            
                            if not description:
                                description = "Unknown merchant"
                            
                            # Create transaction
                            trans_date = parse_short_date(date_str, start_year, end_year, statement_month)
                            
                            # Check if this transaction is already captured
                            is_duplicate = False
                            for t in transactions:
                                if (t['transaction_date'] == trans_date and 
                                    abs(t['amount'] - amount) < 0.01):
                                    is_duplicate = True
                                    break
                            
                            if not is_duplicate:
                                new_transaction = {
                                    'transaction_date': trans_date,
                                    'posting_date': trans_date,  # Use same date for both
                                    'description': description,
                                    'amount': amount,
                                    'foreign_amount': None,
                                    'foreign_currency': None,
                                    'exchange_rate': None
                                }
                                page_transactions.append(new_transaction)
                                if verbose:
                                    print(f"  Added new transaction: {trans_date} | {description} | ${amount:.2f}")
        
        # Add new transactions found
        if page_transactions:
            print(f"Found {len(page_transactions)} additional transactions during thorough analysis.")
            transactions.extend(page_transactions)
    
    print(f"Found total of {len(transactions)} transactions (from {transaction_count} transaction lines).")
    
    # Sort transactions by date
    transactions.sort(key=lambda x: x['transaction_date'])
    
    return transactions

def parse_short_date(date_str, start_year, end_year, statement_month):
    """Parse dates like 'DEC8' into a full date string."""
    # Extract month and day
    month_match = re.match(r'([A-Z]{3})\s*(\d{1,2})', date_str)
    if not month_match:
        # Try alternative formats
        alt_month_match = re.match(r'(\w{3})[-\s\.]*(\d{1,2})', date_str, re.IGNORECASE)
        if not alt_month_match:
            print(f"Warning: Could not parse date format: '{date_str}', returning as is.")
            return date_str
        month_abbr = alt_month_match.group(1).upper()
        day = int(alt_month_match.group(2))
    else:
        month_abbr = month_match.group(1)
        day = int(month_match.group(2))
    
    # Convert month abbreviation to number
    months = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    
    month_num = months.get(month_abbr, 1)
    if month_abbr not in months:
        print(f"Warning: Unknown month abbreviation '{month_abbr}' in date '{date_str}'. Using January.")
    
    # Convert statement_month to a month number for comparison
    statement_month_num = None
    for m, num in months.items():
        if statement_month and statement_month.upper().startswith(m):
            statement_month_num = num
            break
    
    # Determine year based on statement period and month number
    year = end_year  # Default to end_year
    
    # Only apply year adjustments if we have a valid statement month
    if statement_month_num is not None:
        # If transaction is from a month significantly earlier than the statement month,
        # it likely belongs to the end_year (current statement year)
        # If it's from a month significantly later, it might be from the previous year (start_year)
        
        # For statements in the first few months of the year
        if statement_month_num <= 3:  # Jan, Feb, Mar
            if month_num >= 10:  # Oct, Nov, Dec
                # Late months in a statement from early in the year are likely from previous year
                year = start_year
                
        # For statements in the last few months of the year
        elif statement_month_num >= 10:  # Oct, Nov, Dec
            if month_num <= 3:  # Jan, Feb, Mar
                # Early months in a statement from late in the year are likely from next year
                year = end_year
                # Ensure we don't inadvertently use the wrong year based on statement period
                if end_year > start_year:
                    year = end_year
                else:
                    year = start_year + 1
    
    # Format the date
    return f"{year}-{month_num:02d}-{day:02d}"

def save_to_csv(transactions, output_path):
    """Save extracted transactions to a CSV file."""
    if not transactions:
        print("No transactions found to save.")
        return False
        
    try:
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['transaction_date', 'posting_date', 'description', 'amount', 
                          'foreign_amount', 'foreign_currency', 'exchange_rate']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for transaction in transactions:
                writer.writerow(transaction)
                
        print(f"Successfully saved {len(transactions)} transactions to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False

def main():
    """Main function to handle command-line arguments and process the PDF."""
    parser = argparse.ArgumentParser(description='Convert TD credit card statement PDF to CSV')
    parser.add_argument('pdf_path', help='Path to the PDF statement file')
    parser.add_argument('--output', '-o', help='Output CSV file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode with additional output')
    parser.add_argument('--page-analysis', '-p', action='store_true', 
                       help='Analyze each page separately for additional transactions')
    parser.add_argument('--thorough', '-t', action='store_true',
                       help='Enable thorough processing to find more transactions')
    
    args = parser.parse_args()
    
    # Set up verbose mode
    verbose_mode = args.verbose or args.debug
    if args.debug:
        print("Debug mode enabled - showing detailed information")
    if args.thorough:
        print("Thorough processing mode enabled - will try harder to find all transactions")
    
    # Validate input file
    if not os.path.exists(args.pdf_path):
        print(f"Error: File '{args.pdf_path}' does not exist.")
        return 1
        
    # Generate default output path if not specified
    if not args.output:
        basename = os.path.basename(args.pdf_path)
        filename, _ = os.path.splitext(basename)
        args.output = os.path.join("out", f"{filename}.csv")
        
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Process the PDF
    print(f"Processing {args.pdf_path}...")
    
    # Get file info
    if verbose_mode:
        print(f"File size: {os.path.getsize(args.pdf_path) / 1024:.2f} KB")
        
    # Extract transactions
    transactions = extract_transactions(
        pdf_path=args.pdf_path, 
        verbose=verbose_mode,
        thorough=args.thorough or args.page_analysis
    )
    
    if not transactions:
        print("No transactions were found in the PDF.")
        return 1
        
    print(f"Found {len(transactions)} transactions.")
    
    # Print transaction summary in verbose mode
    if verbose_mode:
        total_amount = sum(t['amount'] for t in transactions)
        print(f"Total transaction amount: ${total_amount:.2f}")
        if args.debug:
            for i, t in enumerate(transactions):
                print(f"Transaction {i+1}: {t['transaction_date']} - {t['description']} - ${t['amount']:.2f}")
    
    # Save to CSV
    save_to_csv(transactions, args.output)
    
    return 0

if __name__ == "__main__":
    exit(main()) 