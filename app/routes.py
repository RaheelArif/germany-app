from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
import os
import uuid
import pandas as pd
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
    if menu_type in ['germany']:
        return render_template('upload.html', menu_type=menu_type)  # Redirect to the upload page for extraction
    elif menu_type in ['sweden']:
        return render_template('code_input.html', menu_type=menu_type)
    else:
        return redirect(url_for('main.home'))
    
@main.route('/verify_code', methods=['POST'])
def verify_code():
    code = request.form.get('code')
    correct_code = "Anas@$2771972"  # Replace with the actual correct code

    if code == correct_code:
        return redirect(url_for('main.menu_options'))
    else:
        flash('Invalid code. Please try again.')
        return redirect(url_for('main.menu', menu_type='sweden'))
    
@main.route('/menu_options')
def menu_options():
    return render_template('menu_options.html')

@main.route('/check_quantity')
def check_quantity():
    return "Check Quantity Page"

@main.route('/messages')
def messages():
    return "Messages Page"

@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'menu_type' not in request.form:
        flash('No file part or menu type')
        return redirect(request.url)
    
    file = request.files['file']
    menu_type = request.form['menu_type']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file:
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        
        # Define allowed file types for each program
        allowed_file_types = {
            'germany': ['pdf'],
            'sweden': ['xlsx']
        }
        
        if menu_type not in allowed_file_types or file_extension not in allowed_file_types[menu_type]:
            flash(f'Only {", ".join(allowed_file_types.get(menu_type, []))} files are allowed for {menu_type} program.')
            return redirect(request.url)
        
        filename = f"{uuid.uuid4()}.{file_extension}"
        input_path = os.path.join(current_app.root_path, "uploads", filename)
        file.save(input_path)

        # Ensure the downloads directory exists
        downloads_path = os.path.join(current_app.root_path, 'downloads')
        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path)
        
        return redirect(url_for('main.process_file', filename=filename))

@main.route('/process_file/<filename>', methods=['GET'])
def process_file(filename):
    file_extension = filename.rsplit('.', 1)[1].lower()
    input_path = os.path.join(current_app.root_path, "uploads", filename)
    downloads_path = os.path.join(current_app.root_path, 'downloads')

    if file_extension == 'pdf':
        return process_pdf_file(input_path, downloads_path, filename)
    else:
        return process_spreadsheet_file(input_path, downloads_path, filename, file_extension)

def process_pdf_file(input_path, downloads_path, filename):
    # Process the PDF
    margins = (33.41, 82.56, 52.13, 93.24)  # Left, Top, Right, Bottom in points
    label_size = (255, 133.1)  # Width and height in points
    rows, cols = 5, 2

    pdf_document = load_pdf(input_path)
    label_pdfs = extract_labels(pdf_document, margins, label_size, rows, cols)

    output_pdf_filename = f"labels_{filename}"
    output_text_filename = f"text_{filename.replace('.pdf', '.txt')}"
    output_pdf_path = os.path.join(downloads_path, output_pdf_filename)
    output_text_path = os.path.join(downloads_path, output_text_filename)
    
    compile_labels(label_pdfs, output_pdf_path)

    extracted_texts = extract_text_from_labels(pdf_document, margins, label_size, rows, cols)
    save_extracted_texts(extracted_texts, output_text_path)

    # Cleanup the original upload
    pdf_document.close()  # Ensure the PDF is closed before removing
    os.remove(input_path)

    return redirect(url_for('main.results', labels_pdf=output_pdf_filename, text_file=output_text_filename, label_count=len(label_pdfs)))

import os

def process_pdf_file_and_return_json(input_path, downloads_path, filename):
    try:

        margins = (33.41, 82.56, 52.13, 93.24)  # Left, Top, Right, Bottom in points
        label_size = (255, 133.1)  # Width and height in points
        rows, cols = 5, 2

        pdf_document = load_pdf(input_path)  # Placeholder function
        label_pdfs = extract_labels(pdf_document, margins, label_size, rows, cols)  # Placeholder function

        output_pdf_filename = f"pdf_{filename}"
        output_text_filename = f"text_{filename.replace('.pdf', '.txt')}"

        output_pdf_path = os.path.join(downloads_path, output_pdf_filename)
        output_text_path = os.path.join(downloads_path, output_text_filename)
        
        compile_labels(label_pdfs, output_pdf_path)  # Placeholder function

        extracted_texts = extract_text_from_labels(pdf_document, margins, label_size, rows, cols)  # Placeholder function
        save_extracted_texts(extracted_texts, output_text_path)  # Placeholder function

        os.remove(input_path)

        response = {
            "pdf_file": output_pdf_filename,
            "text_file": output_text_filename,
        }
        return response

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}
    finally:
        # Ensure the PDF is closed safely
        if 'pdf_document' in locals() and pdf_document:
            pdf_document.close()
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except OSError as remove_error:
                print(f"Error removing file: {remove_error}")



def process_spreadsheet_file(input_path, downloads_path, filename, file_extension):
    if file_extension == 'xlsx':
        df = pd.read_excel(input_path)
    
    bad_comments = df[df['Comments'].str.contains('bad', case=False, na=False)]
    
    # Assuming 'links' is a list of URLs from the 'bad_comments' DataFrame
    links = bad_comments['URL'].tolist() if 'URL' in bad_comments.columns else []

    result_html = bad_comments.to_html(classes='data')
    result_path = os.path.join(downloads_path, 'feedback_result.html')
    with open(result_path, 'w') as f:
        f.write(render_template('feedback_result.html', tables=result_html, links=links, download_link=url_for('main.download_result')))
    
    os.remove(input_path)

    return render_template('feedback_result.html', tables=result_html, links=links, download_link=url_for('main.download_result'))

@main.route('/results')
def results():
    labels_pdf = request.args.get('labels_pdf')
    text_file = request.args.get('text_file')
    label_count = request.args.get('label_count')
    return render_template('results.html', labels_pdf=labels_pdf, text_file=text_file, label_count=label_count)

@main.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    downloads_folder = os.path.join(current_app.root_path, 'downloads')
    file_path = os.path.join(downloads_folder, filename)
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    return send_file(file_path, as_attachment=True)
