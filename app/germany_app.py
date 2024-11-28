from flask import Blueprint, request, abort, jsonify, current_app, send_file
from flask_cors import cross_origin
import os
import uuid
from .routes import process_pdf_file_and_return_json

# Create blueprint with url_prefix
germany_section = Blueprint('germany_section', __name__, url_prefix='/api/germany_section')

@germany_section.route('/home', methods=['GET'])
@cross_origin()
def home():
    response = {
        'message': 'Welcome to the Germany Section Home Page'
    }
    return jsonify(response)

@germany_section.route('/pdf_upload', methods=['POST', 'OPTIONS'])
@cross_origin()
def pdf_upload():
    try:
        if request.method == 'OPTIONS':
            return jsonify({'message': 'ok'}), 200

        print("Upload request received")  # Debug log

        if 'file' not in request.files:
            print("No file in request")  # Debug log
            abort(400, description="No selected file")
        
        file = request.files['file']
        print(f"File received: {file.filename}")  # Debug log
        
        if file.filename == '':
            print("Empty filename")  # Debug log
            abort(400, description="No selected file")

        file_extension = file.filename.rsplit('.', 1)[1].lower()
        print(f"File extension: {file_extension}")  # Debug log
        
        allowed_file_types = ['pdf']
        
        if file_extension not in allowed_file_types:
            print("Invalid file type")  # Debug log
            abort(400, description=f'Only {", ".join(allowed_file_types)} files are allowed.')

        # Create directories if they don't exist
        upload_dir = os.path.join(current_app.root_path, "uploads")
        downloads_dir = os.path.join(current_app.root_path, "downloads")
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(downloads_dir, exist_ok=True)

        # Save and process file
        filename = f"{uuid.uuid4()}.{file_extension}"
        input_path = os.path.join(upload_dir, filename)
        file.save(input_path)
        print(f"File saved to: {input_path}")  # Debug log

        process_file = process_pdf_file_and_return_json(input_path, downloads_dir, filename)
        
        response = {
            'message': 'File has been uploaded',
            'file_name': filename,
            'processed_file_location': process_file
        }
        return jsonify(response)

    except Exception as e:
        print(f"Error in pdf_upload: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@germany_section.route('/download/<path:filename>', methods=['GET'])
@cross_origin()
def download_file(filename):
    try:
        downloads_folder = os.path.join(current_app.root_path, 'downloads')
        file_path = os.path.join(downloads_folder, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        print(f"Error in download: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500