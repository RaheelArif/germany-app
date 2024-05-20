import os
from flask import Flask, request, send_file, render_template
import fitz
import zipfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['LABEL_FOLDER'] = 'labels'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['LABEL_FOLDER']):
    os.makedirs(app.config['LABEL_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        return "No file part"
    
    files = request.files.getlist('files[]')
    if len(files) == 0:
        return "No selected files"

    labels = []
    for file in files:
        if file and file.filename:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            labels.extend(process_pdf(filepath))
    
    return render_template('result.html', labels=labels)

def process_pdf(filepath):
    print(f"Processing PDF: {filepath}")
    pdf_document = fitz.open(filepath)

    top_crop = 1.1467 * 72  # 1.2 inches
    bottom_crop = 1.295 * 72  # 1.2 inches
    left_crop = 0.464 * 72  # 0.5 inches
    right_crop = 0.724 * 72  # 0.5 inches

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        rect = page.rect
        new_rect = fitz.Rect(rect.x0 + left_crop, rect.y0 + top_crop, rect.x1 - right_crop, rect.y1 - bottom_crop)
        page.set_cropbox(new_rect)

    cropped_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cropped_' + os.path.basename(filepath))
    pdf_document.save(cropped_pdf_path)
    print(f"Cropped PDF saved as: {cropped_pdf_path}")

    cropped_pdf = fitz.open(cropped_pdf_path)
    label_width = 3.5 * 72  # 3.5 inches in points
    label_height = 1.9 * 72  # 1.9 inches in points

    label_coords = []
    for row in range(5):
        for col in range(2):
            if len(label_coords) >= 10:
                break
            x0 = col * label_width
            y0 = row * label_height
            x1 = x0 + label_width
            y1 = y0 + label_height
            label_coords.append((x0, y0, x1, y1))

    output_files = []
    for page_num in range(len(cropped_pdf)):
        for idx, (x0, y0, x1, y1) in enumerate(label_coords):
            try:
                rect = fitz.Rect(x0, y0, x1, y1)
                page = cropped_pdf.load_page(page_num)
                text_content = page.get_text("text", clip=rect).strip()
                if len(text_content) == 0:
                    print(f"No content found in region for Label {idx + 1} on page {page_num + 1}, stopping extraction.")
                    break

                new_pdf = fitz.open()
                new_page = new_pdf.new_page(width=rect.width, height=rect.height)
                new_page.show_pdf_page(new_page.rect, cropped_pdf, page_num, clip=rect)

                output_pdf_path = os.path.join(app.config['LABEL_FOLDER'], f"label_{page_num + 1}_{idx + 1}.pdf")
                new_pdf.save(output_pdf_path)
                new_pdf.close()
                output_files.append(f"label_{page_num + 1}_{idx + 1}.pdf")
                print(f"Label {idx + 1} on page {page_num + 1} saved as {output_pdf_path}")
            except Exception as e:
                print(f"Failed to process label {idx + 1} on page {page_num + 1}: {e}")

    print(f"Output files: {output_files}")
    return output_files

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['LABEL_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404

@app.route('/download_all')
def download_all():
    zip_filename = os.path.join(app.config['LABEL_FOLDER'], 'labels.zip')
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, _, files in os.walk(app.config['LABEL_FOLDER']):
            for file in files:
                if file.endswith('.pdf'):
                    zipf.write(os.path.join(root, file), file)
    return send_file(zip_filename, as_attachment=True)

@app.route('/print_labels')
def print_labels():
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    label_width = 3.5 * 72  # 3.5 inches in points
    label_height = 1.9 * 72  # 1.9 inches in points

    print_pdf_path = os.path.join(app.config['LABEL_FOLDER'], 'print_labels.pdf')
    c = canvas.Canvas(print_pdf_path, pagesize=letter)
    width, height = letter

    y_position = height - 40  # start from top, margin 40
    label_margin = 10  # margin between labels

    for root, _, files in os.walk(app.config['LABEL_FOLDER']):
        for file in sorted(files):
            if file.endswith('.pdf'):
                label_path = os.path.join(root, file)
                c.drawImage(label_path, 40, y_position - 100, width=label_width, height=label_height)
                y_position -= (label_height + label_margin)
                if y_position < label_height + 40:  # check if need new page
                    c.showPage()
                    y_position = height - 40

    c.save()
    return send_file(print_pdf_path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
