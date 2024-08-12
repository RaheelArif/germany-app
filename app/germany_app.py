from flask import Flask, request, abort, jsonify, current_app, Blueprint, send_file
import os
import uuid

from .routes import process_pdf_file_and_return_json


germany_section = Blueprint('germany_section', __name__)

@germany_section.route('/api/germany_section/home',methods=['GET'])
def home():
    response = {
        'message': 'Welcome to the Germany Section Home Page'
    }
    return jsonify(response)


@germany_section.route('/api/germany_section/pdf_upload',methods=['POST'])
def pdf_upload():

    if 'file' not in request.files:
        abort(400, description="No selected file")
    
    file = request.files['file']
    
    if file.filename == '':
        abort(400, description="No selected file")

    
    if file:
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        

        print(file_extension)
        # Define allowed file types for each program
        # Define allowed file types
        allowed_file_types = ['pdf']
        
        if file_extension not in allowed_file_types:
            abort(400, description=f'Only {", ".join(allowed_file_types)} files are allowed.')


        filename = f"{uuid.uuid4()}.{file_extension}"
        input_path = os.path.join(current_app.root_path, "uploads", filename)
        file.save(input_path)

        # Ensure the downloads directory exists
        downloads_path = os.path.join(current_app.root_path, 'downloads')
        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path)

        downloads_path = os.path.join(current_app.root_path, 'downloads')

        
        process_file = process_pdf_file_and_return_json(input_path, downloads_path ,filename)
        response = {
        'message': 'File has been uploaded',
        'file_name': filename,
        'processed_file_location': process_file
        }
        return jsonify(response)



@germany_section.route('/api/germany_section/download/<path:filename>', methods=['GET'])
def download_file(filename):
    downloads_folder = os.path.join(current_app.root_path, 'downloads')
    file_path = os.path.join(downloads_folder, filename)
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    return send_file(file_path, as_attachment=True)