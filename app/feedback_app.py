from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, flash
import os
import pandas as pd
from werkzeug.utils import secure_filename

feedback = Blueprint('feedback', __name__)

UPLOAD_FOLDER = 'app/uploads'
RESULT_FOLDER = 'app/results'
ALLOWED_EXTENSIONS = {'xlsx'}

# Ensure the upload and result directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@feedback.route('/check_bad_comments')
def check_bad_comments():
    return render_template('feedback_index.html')

@feedback.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return redirect(url_for('feedback.process_file', filename=filename))
    else:
        flash('Allowed file types are .xlsx')
        return redirect(request.url)

@feedback.route('/process_file/<filename>')
def process_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    df = pd.read_excel(filepath)
    bad_comments = df[df['Comments'].str.contains('bad', case=False, na=False)]
    result_html = bad_comments.to_html(classes='data')
    result_path = os.path.join(RESULT_FOLDER, 'feedback_result.html')
    with open(result_path, 'w') as f:
        f.write(render_template('feedback_result.html', tables=result_html, download_link=url_for('feedback.download_result')))
    return render_template('feedback_result.html', tables=result_html, download_link=url_for('feedback.download_result'))

@feedback.route('/download_result')
def download_result():
    return send_from_directory(RESULT_FOLDER, 'feedback_result.html')
