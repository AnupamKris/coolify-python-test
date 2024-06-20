from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime, UTC

# Initialize the Flask application
app = Flask(__name__)
CORS(app)
print(datetime.now(UTC).isoformat())
# Folder to store uploaded files
UPLOAD_FOLDER = 'upload'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# JSON file to store metadata
METADATA_FILE = 'metadata.json'

# Helper function to save metadata
def save_metadata(name, file_path, upload_date):
    metadata = []
    # Load existing metadata if exists
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
    
    # Append new metadata
    metadata.append({
        'name': name,
        'filePath': file_path,
        'date': upload_date
    })

    # Save updated metadata
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=4)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'name' not in request.form:
        return jsonify({'error': 'No file or name provided'}), 400

    file = request.files['file']
    name = request.form['name']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.pdf'):
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}.pdf"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        upload_date = datetime.now(UTC).isoformat()
        # change date to dd-mm-yyyy
        upload_date = "/".join(upload_date.split('T')[0].split("-")[::-1])
        save_metadata(name, unique_id, upload_date)

        return jsonify({'message': 'File successfully uploaded', 'filePath': file_path, 'date': upload_date}), 201

    return jsonify({'error': 'Invalid file type, only PDF files are allowed'}), 400


@app.route('/documents', methods=['GET'])
def get_documents():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        return jsonify(metadata), 200
    return jsonify({'error': 'No documents found'}), 404

@app.route('/download/<path:unique_id>', methods=['GET'])
def download_file(unique_id):
    try:
        # Construct the file path
        file_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.pdf")
        # Send the file for download
        
        return send_from_directory(UPLOAD_FOLDER, f"{unique_id}.pdf", as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/delete', methods=['POST'])
def delete_file():
    data = request.get_json()
    if not data or 'filePath' not in data:
        return jsonify({'error': 'File path not provided'}), 400

    file_path = UPLOAD_FOLDER + os.sep + data['filePath'] + '.pdf'
    print(file_path)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            # Remove the record from the metadata file
            if os.path.exists(METADATA_FILE):
                with open(METADATA_FILE, 'r') as f:
                    metadata = json.load(f)
                metadata = [entry for entry in metadata if entry['filePath'] != data['filePath']]
                with open(METADATA_FILE, 'w') as f:
                    json.dump(metadata, f, indent=4)
            return jsonify({'message': 'File successfully deleted'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'File not found'}), 404

@app.route('/', methods=['GET'])
def index():
    return "HEELLLO WORLD"

if __name__ == '__main__':
    app.run(debug=True)
