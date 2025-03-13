from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import uuid #generates unique identifiers
import datetime #supplies classes for manipulating dates and times
import mimetypes #maps filenames to MIME types
import logging # provides a way to configure logging
from werkzeug.utils import secure_filename #ensures filenames are save
from functools import wraps # a decorator to preserve the original function's metadata

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'csv'}
app.secret_key = os.environ.get('SECRET_KEY', 'development-key')  # For sessions

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Basic authentication (for demonstration)
API_KEY = os.environ.get('API_KEY', 'test-api-key')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            return f(*args, **kwargs)
        return jsonify({"error": "Unauthorized access"}), 401
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Database simulation - in a real app, you'd use a proper database
file_metadata = {}


@app.route('/')
def index():
    # Use the inline HTML directly instead of looking for a template file
    return get_index_template()

@app.route('/upload', methods=['POST'])
@require_api_key
def upload_file():
    try:
        if 'file' not in request.files:
            logger.warning("No file part in request")
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']

        if file.filename == '':
            logger.warning("No selected file")
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            # Create a unique filename to prevent overwrites
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else f"{uuid.uuid4().hex}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Store metadata
            file_metadata[unique_filename] = {
                'original_filename': original_filename,
                'upload_time': datetime.datetime.now().isoformat(),
                'size': os.path.getsize(filepath),
                'mime_type': mimetypes.guess_type(original_filename)[0],
                'uploader_ip': request.remote_addr
            }
            
            logger.info(f"File uploaded successfully: {original_filename} as {unique_filename}")
            
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': unique_filename,
                'original_filename': original_filename,
                'download_url': f"/download/{unique_filename}"
            }), 201
        else:
            logger.warning(f"File type not allowed: {file.filename}")
            return jsonify({'error': 'File type not allowed'}), 400
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': f'File upload failed: {str(e)}'}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # Check if file exists
        if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            logger.warning(f"File not found: {filename}")
            return jsonify({'error': 'File not found'}), 404
        
        # Get original filename for display if available
        original_filename = file_metadata.get(filename, {}).get('original_filename', filename)
        
        logger.info(f"File downloaded: {filename} (original: {original_filename})")
        
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            filename, 
            as_attachment=True,
            download_name=original_filename
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/files', methods=['GET'])
@require_api_key
def list_files():
    try:
        files = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                file_info = file_metadata.get(filename, {})
                files.append({
                    'filename': filename,
                    'original_filename': file_info.get('original_filename', filename),
                    'size': os.path.getsize(file_path),
                    'upload_time': file_info.get('upload_time', 'unknown'),
                    'mime_type': file_info.get('mime_type', 'application/octet-stream'),
                    'download_url': f'/download/{filename}'
                })
        
        logger.info(f"File list requested, {len(files)} files returned")
        return jsonify({'files': files})
    
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({'error': f'Could not list files: {str(e)}'}), 500

@app.route('/files/<filename>', methods=['DELETE'])
@require_api_key
def delete_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            logger.warning(f"Attempted to delete non-existent file: {filename}")
            return jsonify({'error': 'File not found'}), 404
        
        os.remove(file_path)
        
        # Remove metadata
        if filename in file_metadata:
            del file_metadata[filename]
        
        logger.info(f"File deleted: {filename}")
        return jsonify({'message': 'File deleted successfully'})
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return jsonify({'error': f'Could not delete file: {str(e)}'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    logger.warning("File too large")
    return jsonify({'error': 'File too large. Maximum file size is 16MB'}), 413

# HTML template for the index page
@app.route('/templates/index.html')
def get_index_template():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>File Upload API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            .endpoint { background: #f5f5f5; padding: 15px; margin-bottom: 15px; border-radius: 5px; }
            .method { font-weight: bold; display: inline-block; width: 80px; }
            .url { font-family: monospace; }
            pre { background: #f0f0f0; padding: 10px; border-radius: 3px; overflow: auto; }
            form { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
            button { background: #4CAF50; color: white; border: none; padding: 10px 15px; cursor: pointer; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>File Upload and Download API</h1>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <span class="url">/upload</span>
            <p>Upload a file. Requires X-API-Key header.</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <span class="url">/download/{filename}</span>
            <p>Download a specific file by its filename.</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <span class="url">/files</span>
            <p>List all uploaded files. Requires X-API-Key header.</p>
        </div>
        
        <div class="endpoint">
            <span class="method">DELETE</span>
            <span class="url">/files/{filename}</span>
            <p>Delete a specific file by its filename. Requires X-API-Key header.</p>
        </div>
        
        <h2>Try it out</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <div>
                <label for="api-key">API Key:</label>
                <input type="text" id="api-key" name="api-key" placeholder="Enter your API key">
            </div>
            <div style="margin-top: 10px;">
                <input type="file" name="file">
            </div>
            <div style="margin-top: 10px;">
                <button type="button" onclick="uploadFile()">Upload</button>
            </div>
        </form>
        
        <div id="result"></div>
        
        <script>
            function uploadFile() {
                const fileInput = document.querySelector('input[type="file"]');
                const apiKey = document.querySelector('#api-key').value;
                
                if (!fileInput.files.length) {
                    alert('Please select a file first');
                    return;
                }
                
                if (!apiKey) {
                    alert('Please enter an API key');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                fetch('/upload', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-API-Key': apiKey
                    }
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('result').innerHTML = `
                        <h3>Result:</h3>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                        ${data.download_url ? `<p><a href="${data.download_url}" target="_blank">Download file</a></p>` : ''}
                    `;
                })
                .catch(error => {
                    document.getElementById('result').innerHTML = `
                        <h3>Error:</h3>
                        <pre>${error}</pre>
                    `;
                });
            }
        </script>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    app.run(debug=True)