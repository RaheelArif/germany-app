from flask import Blueprint, render_template, request, send_file, redirect, url_for
import os
import uuid
from .pdf_utils import (load_pdf, extract_labels, compile_labels, extract_text_from_labels, save_extracted_texts)

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/upload_logo', methods=['POST'])
def upload_logo():
    if 'logo' not in request.files:
        return redirect(request.url)
    
    file = request.files['logo']
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        logo_path = os.path.join("static/images", "logo.png")
        file.save(logo_path)
        return redirect(url_for('main.home'))

@main.route('/menu/<menu_type>')
def menu(menu_type):
    if menu_type in ['sweden', 'sweden_with_flags']:
        return render_template('upload.html')  # Redirect to the upload page for extraction
    else:
        return redirect(url_for('main.home'))

@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        filename = str(uuid.uuid4()) + ".pdf"
        input_path = os.path.join("uploads", filename)
        file.save(input_path)
        
        # Ensure the downloads directory exists
        if not os.path.exists('downloads'):
            os.makedirs('downloads')
        
        # Process the PDF
        margins = (33.41, 82.56, 52.13, 93.24)  # Left, Top, Right, Bottom in points
        label_size = (255, 133.1)  # Width and height in points
        rows, cols = 5, 2

        pdf_document = load_pdf(input_path)
        label_pdfs = extract_labels(pdf_document, margins, label_size, rows, cols)

        output_pdf_path = os.path.join("downloads", f"labels_{filename}")
        compile_labels(label_pdfs, output_pdf_path)

        extracted_texts = extract_text_from_labels(pdf_document, margins, label_size, rows, cols)
        output_text_path = os.path.join("downloads", f"text_{filename.replace('.pdf', '.txt')}")
        save_extracted_texts(extracted_texts, output_text_path)

        # Cleanup the original upload
        pdf_document.close()  # Ensure the PDF is closed before removing
        os.remove(input_path)

        return redirect(url_for('main.results', labels_pdf=output_pdf_path, text_file=output_text_path, label_count=len(label_pdfs)))

@main.route('/results')
def results():
    labels_pdf = request.args.get('labels_pdf')
    text_file = request.args.get('text_file')
    label_count = request.args.get('label_count')
    return render_template('results.html', labels_pdf=labels_pdf, text_file=text_file, label_count=label_count)

@main.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_file(filename, as_attachment=True)
