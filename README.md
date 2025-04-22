# PDF to CSV Converter for Credit Card Statements

This tool converts TD Credit Card statement PDFs to CSV format for easy import into spreadsheets. It extracts transaction information including dates, descriptions, amounts, and foreign currency details.

## Features

- Extracts transaction data from TD credit card statements
- Handles foreign currency transactions and exchange rates
- Correctly processes dates across statement periods
- Outputs CSV files ready for import into budgeting software or spreadsheets

## Requirements

- Python 3.6 or higher
- PyPDF2 library (3.0.0 or higher)

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script with the path to your PDF statement:

```bash
python pdf_to_csv.py "in/your_statement.pdf"
```

By default, the CSV file will be saved to the "out" directory. You can specify a custom output path:

```bash
python pdf_to_csv.py "in/your_statement.pdf" --output "path/to/output.csv"
```

### Processing Multiple PDF Files

To process all PDF files in the input directory at once:

```bash
python process_all_pdfs.py
```

This will convert all PDF files in the "in" directory to CSV files in the "out" directory.

#### Options for process_all_pdfs.py

- `--input`, `-i`: Specify the input directory containing PDF files (default: "in")
- `--output`, `-o`: Specify the output directory for CSV files (default: "out")
- `--verbose`, `-v`: Enable verbose output for debugging
- `--thorough`, `-t`: Enable thorough processing for PDFs with non-standard formatting

Example with custom directories:

```bash
python process_all_pdfs.py --input "statements" --output "converted"
```

### Single File Options

- `--output`, `-o`: Specify the output CSV file path
- `--verbose`, `-v`: Enable verbose output for debugging

## Example

```bash
python pdf_to_csv.py in/TD_Visa_Statement.pdf
```

## CSV Output Format

The generated CSV file includes the following columns:

- `transaction_date`: The date the transaction occurred
- `posting_date`: The date the transaction was posted to your account
- `description`: Description of the transaction
- `amount`: Transaction amount in your account currency
- `foreign_amount`: Original amount for foreign transactions (if applicable)
- `foreign_currency`: Currency code for foreign transactions (if applicable)
- `exchange_rate`: Exchange rate applied to foreign transactions (if applicable)

## Date Parsing

The script intelligently handles date parsing across statement periods:

- Extracts statement date and period from the PDF to determine the correct year for each transaction
- Handles transactions that span across month/year boundaries
- Correctly assigns years to transactions when a statement covers two different years
- Parses short date formats (e.g., "JAN15") into standardized ISO format (YYYY-MM-DD)
- Adjusts transaction years based on the statement month to ensure accuracy

## Combining CSV Files

After converting multiple statements to CSV, you can combine them into a single file:

```bash
python combine_csv.py
```

This will:
- Merge all CSV files from the "out" directory
- Sort transactions by date
- Remove any duplicates
- Save the combined data to "combined.csv" in the main directory

## Limitations

- Currently optimized for TD credit card statements
- Requires statements to be in PDF format
- May require adjustments for other credit card providers

## License

This project is open source. 