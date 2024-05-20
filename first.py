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
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file"

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        labels = process_pdf(filepath)
        return render_template('result.html', labels=labels)

def process_pdf(filepath):
    print(f"Processing PDF: {filepath}")
    
    # Load the original PDF
    pdf_document = fitz.open(filepath)

    # Define the crop margins in points (1 inch = 72 points)
    top_crop = 1.1467 * 72  # 1.2 inches
    bottom_crop = 1.295 * 72  # 1.2 inches
    left_crop = 0.464 * 72  # 0.5 inches
    right_crop = 0.724 * 72  # 0.5 inches

    # Crop the page to remove the margins
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        rect = page.rect
        new_rect = fitz.Rect(rect.x0 + left_crop, rect.y0 + top_crop, rect.x1 - right_crop, rect.y1 - bottom_crop)
        page.set_cropbox(new_rect)

    # Save the cropped PDF
    cropped_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cropped_' + os.path.basename(filepath))
    pdf_document.save(cropped_pdf_path)
    print(f"Cropped PDF saved as: {cropped_pdf_path}")

    # Load the cropped PDF for label extraction
    cropped_pdf = fitz.open(cropped_pdf_path)

    # Define the measurements in points
    label_width = 250  # 3.5 inches
    label_height = 132  # 1.9 inches

    # Calculate label coordinates without spacing
    label_coords = []
    for row in range(5):  # up to 5 rows
        for col in range(2):  # 2 labels per row
            if len(label_coords) >= 10:  # Maximum 10 labels per page
                break
            x0 = col * label_width
            y0 = row * label_height
            x1 = x0 + label_width
            y1 = y0 + label_height
            label_coords.append((x0, y0, x1, y1))

    # Extracting the labels based on the new calculated coordinates and saving them to individual files
    output_files = []
    for idx, (x0, y0, x1, y1) in enumerate(label_coords):
        try:
            rect = fitz.Rect(x0, y0, x1, y1)
            page = cropped_pdf.load_page(0)

            # Check if there is text content in the region
            text_content = page.get_text("text", clip=rect).strip()
            if len(text_content) == 0:
                print(f"No content found in region for Label {idx + 1}, stopping extraction.")
                break

            new_pdf = fitz.open()
            new_page = new_pdf.new_page(width=rect.width, height=rect.height)

            # Directly transfer content without converting to an image
            new_page.show_pdf_page(new_page.rect, cropped_pdf, 0, clip=rect)

            output_pdf_path = os.path.join(app.config['LABEL_FOLDER'], f"label_{idx + 1}.pdf")
            new_pdf.save(output_pdf_path)
            new_pdf.close()
            output_files.append(f"label_{idx + 1}.pdf")
            print(f"Label {idx + 1} saved as {output_pdf_path}")
        except Exception as e:
            print(f"Failed to process label {idx + 1}: {e}")

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
