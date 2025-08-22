from docquery import document, pipeline
import os
import shutil
import re
from datetime import datetime

UNKNOWN_ATTRIBUTE_TEXT = "UNKNOWN"

def answer_invoice_questions(invoice_path: str) -> dict:
    """
    Basic script for getting details about an invoice
    Takes in invoice path

    - Return: res - output of the bot in the form: Company Name, Invoice Number, Invoice total, Date
    """
    try:
        p = pipeline("document-question-answering")
        doc = document.load_document(invoice_path)
        res = {
            "company_name": UNKNOWN_ATTRIBUTE_TEXT,
            "invoice_number": UNKNOWN_ATTRIBUTE_TEXT,
            "invoice_total": UNKNOWN_ATTRIBUTE_TEXT,
            "date": UNKNOWN_ATTRIBUTE_TEXT
        }

        # Helper function to safely extract answer from pipeline response
        def extract_answer(pipeline_response):
            try:
                if isinstance(pipeline_response, dict):
                    return pipeline_response.get('answer', UNKNOWN_ATTRIBUTE_TEXT)
                elif isinstance(pipeline_response, list) and len(pipeline_response) > 0:
                    if isinstance(pipeline_response[0], dict):
                        return pipeline_response[0].get('answer', UNKNOWN_ATTRIBUTE_TEXT)
                    else:
                        return str(pipeline_response[0])
                elif isinstance(pipeline_response, str):
                    return pipeline_response
                else:
                    return UNKNOWN_ATTRIBUTE_TEXT
            except Exception as e:
                print(f"Error extracting answer: {e}")
                return UNKNOWN_ATTRIBUTE_TEXT

        # Process each question with error handling
        try:
            company_response = p(question="What is the company name", **doc.context)
            res["company_name"] = extract_answer(company_response)
        except Exception as e:
            print(f"Error getting company name: {e}")
            res["company_name"] = UNKNOWN_ATTRIBUTE_TEXT

        try:
            invoice_response = p(question="What is the invoice number", **doc.context)
            res["invoice_number"] = extract_answer(invoice_response)
        except Exception as e:
            print(f"Error getting invoice number: {e}")
            res["invoice_number"] = UNKNOWN_ATTRIBUTE_TEXT

        try:
            total_response = p(question="What is the invoice total", **doc.context)
            res["invoice_total"] = extract_answer(total_response)
        except Exception as e:
            print(f"Error getting invoice total: {e}")
            res["invoice_total"] = UNKNOWN_ATTRIBUTE_TEXT

        try:
            date_response = p(question="What is the date", **doc.context)
            res["date"] = extract_answer(date_response)
        except Exception as e:
            print(f"Error getting date: {e}")
            res["date"] = UNKNOWN_ATTRIBUTE_TEXT

        return res

    except Exception as e:
        print(f"Error in answer_invoice_questions: {e}")
        return {
            "company_name": UNKNOWN_ATTRIBUTE_TEXT,
            "invoice_number": UNKNOWN_ATTRIBUTE_TEXT,
            "invoice_total": UNKNOWN_ATTRIBUTE_TEXT,
            "date": UNKNOWN_ATTRIBUTE_TEXT
        }

def clean_company_name(company_name: str) -> str:
    """
    Cleans company name by removing special characters and limiting length
    """
    if company_name == UNKNOWN_ATTRIBUTE_TEXT:
        return company_name
    
    # Remove special characters that aren't allowed in filenames
    cleaned = re.sub(r'[<>:"/\\|?*]', '', company_name)
    # removing websites
    cleaned = re.sub(r'^www\.', '', cleaned)
    cleaned = re.sub(r'\.com$', '', cleaned)
    # Replace spaces and other separators with underscores
    cleaned = re.sub(r'[\s\-\.]+', '_', cleaned)
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    # Limit length
    cleaned = cleaned[:50] if len(cleaned) > 50 else cleaned
    
    return cleaned if cleaned else UNKNOWN_ATTRIBUTE_TEXT

def clean_invoice_number(invoice_number: str) -> str:
    """
    Cleans invoice number by removing special characters
    """
    if invoice_number == UNKNOWN_ATTRIBUTE_TEXT:
        return invoice_number
    
    # Remove special characters that aren't allowed in filenames
    cleaned = re.sub(r'[<>:"/\\|?*\s]', '', invoice_number)
    # Keep alphanumeric and common separators
    cleaned = re.sub(r'[^a-zA-Z0-9\-_]', '', cleaned)
    
    return cleaned if cleaned else UNKNOWN_ATTRIBUTE_TEXT

def clean_invoice_total(invoice_total: str) -> str:
    """
    Cleans invoice total by extracting numeric value and currency
    """
    if invoice_total == UNKNOWN_ATTRIBUTE_TEXT:
        return invoice_total
    
    # Remove special characters except numbers, dots, commas, and common currency symbols
    cleaned = re.sub(r'[<>:"/\\|?*]', '', invoice_total)
    # Remove extra spaces
    cleaned = re.sub(r'\s+', '', cleaned)
    # Keep only numbers, dots, commas, and currency symbols
    cleaned = re.sub(r'[^0-9\.\,\$€£¥]', '', cleaned)
    
    return cleaned if cleaned else UNKNOWN_ATTRIBUTE_TEXT

def clean_date(date: str) -> str:
    """
    Cleans date attribute and standardizes format
    """
    if date == UNKNOWN_ATTRIBUTE_TEXT:
        return date
    
    # Try to parse and reformat common date formats
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
        r'(\d{2,4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD
        r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{2,4})',  # DD Month YYYY
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2}),?\s+(\d{2,4})',  # Month DD, YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date, re.IGNORECASE)
        if match:
            try:
                # Convert to YYYY-MM-DD format
                groups = match.groups()
                if len(groups) == 3:
                    if groups[0].isdigit() and groups[1].isdigit() and groups[2].isdigit():
                        # Numeric date
                        if len(groups[2]) == 4:  # YYYY/MM/DD
                            return f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
                        else:  # MM/DD/YY or DD/MM/YY
                            year = int(groups[2]) + 2000 if int(groups[2]) < 50 else int(groups[2]) + 1900
                            return f"{year}-{groups[0].zfill(2)}-{groups[1].zfill(2)}"
            except:
                pass
    
    # If no pattern matches, clean special characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '', date)
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    
    return cleaned if cleaned else UNKNOWN_ATTRIBUTE_TEXT

def clean_all(invoice_data: dict) -> dict:
    """
    Cleans all attributes of the invoice data
    """
    invoice_data["company_name"] = clean_company_name(invoice_data["company_name"])
    invoice_data["invoice_number"] = clean_invoice_number(invoice_data["invoice_number"])
    invoice_data["invoice_total"] = clean_invoice_total(invoice_data["invoice_total"])
    invoice_data["date"] = clean_date(invoice_data["date"])

    return invoice_data

def create_new_name(invoice_data: dict) -> str:
    """
    Create a new name for the invoice based on its contents
    Assumes that invoice data is already clean
    """
    company_name = invoice_data["company_name"]
    invoice_number = invoice_data["invoice_number"]
    invoice_total = invoice_data["invoice_total"]
    date = invoice_data["date"]

    # Create filename components, replacing UNKNOWN with fallback values
    components = []
    
    if company_name != UNKNOWN_ATTRIBUTE_TEXT:
        components.append(company_name)
    else:
        components.append("UnknownCompany")
    
    if invoice_number != UNKNOWN_ATTRIBUTE_TEXT:
        components.append(invoice_number)
    else:
        components.append("NoNumber")
    
    if date != UNKNOWN_ATTRIBUTE_TEXT:
        components.append(date)
    else:
        components.append(datetime.now().strftime("%Y-%m-%d"))
    
    if invoice_total != UNKNOWN_ATTRIBUTE_TEXT:
        components.append(invoice_total)
    else:
        components.append("NoAmount")

    # Join components with underscores and add PDF extension
    filename = "_".join(components) + ".pdf"
    
    # Ensure filename isn't too long (Windows has 255 char limit)
    if len(filename) > 200:
        filename = filename[:200] + ".pdf"
    
    return filename

def rename_file(old_path: str, new_name: str) -> str:
    """
    Rename a file and return the new path
    """
    directory = os.path.dirname(old_path)
    new_path = os.path.join(directory, new_name)
    
    # Handle case where new filename already exists
    counter = 1
    base_name, ext = os.path.splitext(new_name)
    while os.path.exists(new_path):
        new_name_with_counter = f"{base_name}_{counter}{ext}"
        new_path = os.path.join(directory, new_name_with_counter)
        counter += 1
    
    os.rename(old_path, new_path)
    return new_path

def process_single_invoice(file_path: str, output_directory: str = None) -> dict:
    """
    Process a single invoice file: extract data, clean it, rename file
    
    Args:
        file_path: Path to the invoice file
        output_directory: Directory to save renamed file (optional, defaults to same directory)
    
    Returns:
        Dictionary with processing results
    """
    try:
        # Extract invoice data
        invoice_data = answer_invoice_questions(file_path)
        
        # Clean the extracted data
        cleaned_data = clean_all(invoice_data)
        
        # Create new filename
        new_filename = create_new_name(cleaned_data)
        
        # Determine output path
        if output_directory:
            os.makedirs(output_directory, exist_ok=True)
            new_path = os.path.join(output_directory, new_filename)
            # Copy file to new location with new name
            shutil.copy2(file_path, new_path)
        else:
            # Rename in place
            new_path = rename_file(file_path, new_filename)
        
        return {
            "success": True,
            "original_path": file_path,
            "new_path": new_path,
            "new_filename": new_filename,
            "invoice_data": cleaned_data
        }
        
    except Exception as e:
        return {
            "success": False,
            "original_path": file_path,
            "error": str(e),
            "invoice_data": None
        }

def process_multiple_invoices(file_paths: list, output_directory: str = None) -> list:
    """
    Process multiple invoice files
    
    Args:
        file_paths: List of paths to invoice files
        output_directory: Directory to save renamed files (optional)
    
    Returns:
        List of processing results for each file
    """
    results = []
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            result = process_single_invoice(file_path, output_directory)
            results.append(result)
        else:
            results.append({
                "success": False,
                "original_path": file_path,
                "error": "File not found",
                "invoice_data": None
            })
    
    return results

def run_invoice_processor(input_directory: str, output_directory: str = None, file_extensions: list = None):
    """
    Run the complete invoice processing pipeline on a directory of files
    
    Args:
        input_directory: Directory containing invoice files
        output_directory: Directory to save renamed files (optional, defaults to input_directory)
        file_extensions: List of file extensions to process (defaults to common invoice formats)
    
    Returns:
        Dictionary with summary of processing results
    """
    if file_extensions is None:
        file_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
    
    # Convert extensions to lowercase for comparison
    file_extensions = [ext.lower() for ext in file_extensions]
    
    # Find all invoice files in the input directory
    invoice_files = []
    if os.path.exists(input_directory):
        for filename in os.listdir(input_directory):
            file_path = os.path.join(input_directory, filename)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(filename.lower())
                if ext in file_extensions:
                    invoice_files.append(file_path)
    
    if not invoice_files:
        return {
            "success": False,
            "message": f"No invoice files found in {input_directory}",
            "processed_files": [],
            "failed_files": []
        }
    
    # Process all found files
    results = process_multiple_invoices(invoice_files, output_directory)
    
    # Separate successful and failed results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    return {
        "success": len(successful) > 0,
        "message": f"Processed {len(successful)} files successfully, {len(failed)} failed",
        "processed_files": successful,
        "failed_files": failed,
        "total_files": len(invoice_files)
    }

# Command line interface for standalone usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bot.py <input_directory> [output_directory]")
        print("Example: python bot.py ./invoices ./renamed_invoices")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist")
        sys.exit(1)
    
    print(f"Processing invoices in: {input_dir}")
    if output_dir:
        print(f"Output directory: {output_dir}")
    else:
        print("Renaming files in place")
    
    results = run_invoice_processor(input_dir, output_dir)
    
    print(f"\n{results['message']}")
    
    if results['processed_files']:
        print("\nSuccessfully processed files:")
        for file_result in results['processed_files']:
            print(f"  • {os.path.basename(file_result['original_path'])} → {file_result['new_filename']}")
    
    if results['failed_files']:
        print("\nFailed to process files:")
        for file_result in results['failed_files']:
            print(f"  • {os.path.basename(file_result['original_path'])}: {file_result['error']}")
    
    print(f"\nTotal files processed: {len(results['processed_files'])}/{results['total_files']}")