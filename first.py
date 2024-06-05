from flask import Flask, render_template, request, send_file, redirect, url_for
import fitz
import os
import logging
import uuid

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='extract_labels.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_pdf(input_path):
    logging.info(f"Loading PDF {input_path}")
    return fitz.open(input_path)

def save_pdf(pdf_document, output_path):
    logging.info(f"Saving PDF to {output_path}")
    pdf_document.save(output_path)
    pdf_document.close()

def crop_pages(pdf_document, margins):
    left_crop, top_crop, right_crop, bottom_crop = margins
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        rect = page.rect
        new_rect = fitz.Rect(rect.x0 + left_crop, rect.y0 + top_crop, rect.x1 - right_crop, rect.y1 - bottom_crop)
        page.set_cropbox(new_rect)
        logging.debug(f"Page {page_num + 1} cropped with margins {margins}")
    return pdf_document

def define_label_coordinates(label_size, rows, cols, new_rect):
    label_width, label_height = label_size
    label_coords = []
    for row in range(rows):
        for col in range(cols):
            x0 = new_rect.x0 + col * label_width
            y0 = new_rect.y0 + row * label_height
            x1 = x0 + label_width
            y1 = y0 + label_height
            label_coords.append((x0, y0, x1, y1))
    logging.debug(f"Label coordinates defined with size {label_size} for {rows} rows and {cols} columns")
    return label_coords

def extract_labels(pdf_document, margins, label_size, rows, cols):
    cropped_pdf = crop_pages(pdf_document, margins)
    label_pdfs = []

    for page_num in range(len(cropped_pdf)):
        page = cropped_pdf.load_page(page_num)
        new_rect = page.rect
        
        label_coords = define_label_coordinates(label_size, rows, cols, new_rect)
        
        for idx, (x0, y0, x1, y1) in enumerate(label_coords):
            rect = fitz.Rect(x0, y0, x1, y1)
            label_page = fitz.open()  # Create a new PDF document
            label_rect = fitz.Rect(0, 0, label_size[0], label_size[1])
            new_page = label_page.new_page(width=label_size[0], height=label_size[1])
            new_page.show_pdf_page(label_rect, pdf_document, page.number, clip=rect)

            # Check if the label page contains any non-white content
            if new_page.get_text().strip():  # Simple text check; refine as needed
                label_pdfs.append(label_page)
                logging.debug(f"Extracted label {idx + 1} from page {page_num + 1}")
            else:
                label_page.close()  # Close empty label page to free resources

    return label_pdfs

def compile_labels(label_pdfs, output_path):
    output_pdf = fitz.open()
    for label_pdf in label_pdfs:
        label_page = label_pdf.load_page(0)
        output_pdf.insert_pdf(label_pdf)
        label_pdf.close()
    save_pdf(output_pdf, output_path)

def extract_text_from_labels(pdf_document, margins, label_size, rows, cols):
    extracted_texts = []
    cropped_pdf = crop_pages(pdf_document, margins)
    
    for page_num in range(len(cropped_pdf)):
        page = cropped_pdf.load_page(page_num)
        new_rect = page.rect
        
        label_coords = define_label_coordinates(label_size, rows, cols, new_rect)
        
        for idx, (x0, y0, x1, y1) in enumerate(label_coords):
            rect = fitz.Rect(x0, y0, x1, y1)
            text = page.get_text("text", clip=rect).strip()
            if text:  # Check if the extracted text is not empty
                label_id = f"Page {page_num + 1} Label {idx + 1}"
                extracted_texts.append(f"{label_id}:\n{text}\n")
                logging.debug(f"Extracted text from {label_id}")
    
    return extracted_texts

def save_extracted_texts(extracted_texts, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for text in extracted_texts:
            f.write(text + '\n')
    logging.info(f"Extracted texts saved to {output_path}")

@app.route('/')
def upload_pdf():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
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

        return redirect(url_for('results', labels_pdf=output_pdf_path, text_file=output_text_path, label_count=len(label_pdfs)))


@app.route('/results')
def results():
    labels_pdf = request.args.get('labels_pdf')
    text_file = request.args.get('text_file')
    label_count = request.args.get('label_count')
    return render_template('results.html', labels_pdf=labels_pdf, text_file=text_file, label_count=label_count)

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)