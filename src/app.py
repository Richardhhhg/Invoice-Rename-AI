from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
import os
import shutil
import zipfile
from io import BytesIO
import tempfile
from bot import answer_invoice_questions, clean_all, create_new_name

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_invoice_file(file_path):
    """
    Process a single invoice file and return the new filename
    """
    try:
        # Get invoice details using your existing bot code
        invoice_data = answer_invoice_questions(file_path)
        
        # Clean the data
        cleaned_data = clean_all(invoice_data)
        
        # Create new filename
        new_filename = create_new_name(cleaned_data)
        
        return new_filename, cleaned_data
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        # Fallback to original filename if processing fails
        original_filename = os.path.basename(file_path)
        return f"processed_{original_filename}", {
            "company_name": "UNKNOWN",
            "invoice_number": "UNKNOWN", 
            "invoice_total": "UNKNOWN",
            "date": "UNKNOWN"
        }

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file upload and processing"""
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        processed_files = []
        
        # Clear previous processed files
        for filename in os.listdir(app.config['PROCESSED_FOLDER']):
            file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        
        for file in files:
            if file and allowed_file(file.filename):
                # Secure the filename
                filename = secure_filename(file.filename)
                
                # Save uploaded file
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                
                # Process the invoice
                new_filename, invoice_data = process_invoice_file(upload_path)
                
                # Copy processed file to processed folder with new name
                processed_path = os.path.join(app.config['PROCESSED_FOLDER'], new_filename)
                shutil.copy2(upload_path, processed_path)
                
                processed_files.append({
                    'original_name': filename,
                    'new_name': new_filename,
                    'invoice_data': invoice_data
                })
                
                # Clean up uploaded file
                os.remove(upload_path)
        
        return jsonify({
            'success': True,
            'processed_files': processed_files,
            'message': f'Successfully processed {len(processed_files)} files'
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/download')
def download_files():
    """Create and serve a zip file containing all processed files, then clear the processed folder"""
    try:
        processed_folder = app.config['PROCESSED_FOLDER']
        
        # Check if there are any files to download
        files_to_zip = [f for f in os.listdir(processed_folder) 
                       if os.path.isfile(os.path.join(processed_folder, f))]
        
        if not files_to_zip:
            return jsonify({'error': 'No processed files available for download'}), 404
        
        # Create a temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            # Add all processed files to the zip
            for filename in files_to_zip:
                file_path = os.path.join(processed_folder, filename)
                zip_file.write(file_path, filename)
        
        temp_zip.close()
        
        # Clear the processed folder after creating the zip
        def cleanup_after_download():
            """Clean up processed files and temp zip after download"""
            try:
                # Remove all files from processed folder
                for filename in os.listdir(processed_folder):
                    file_path = os.path.join(processed_folder, filename)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        
                # Remove the temporary zip file
                if os.path.exists(temp_zip.name):
                    os.unlink(temp_zip.name)
                    
            except Exception as e:
                print(f"Error during cleanup: {e}")
        
        # Send the zip file and schedule cleanup
        response = send_file(
            temp_zip.name,
            as_attachment=True,
            download_name='processed_invoices.zip',
            mimetype='application/zip'
        )
        
        # Register cleanup function to run after response is sent
        @response.call_on_close
        def cleanup():
            cleanup_after_download()
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)