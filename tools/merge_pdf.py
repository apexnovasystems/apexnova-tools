from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify, send_file
from PyPDF2 import PdfMerger, PdfReader
import os
import uuid
from werkzeug.utils import secure_filename
import tempfile
from pathlib import Path

merge_pdf_bp = Blueprint("merge_pdf", __name__, subdomain="mergepdf")

# Configuration
UPLOAD_FOLDER = Path(__file__).resolve().parent.parent / "static/storage/merged_pdfs"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@merge_pdf_bp.route("/", methods=["GET"])
def index_get():
    """Handle GET requests - show the form with any existing merge data"""
    merged_filename = session.get('merged_filename', '')
    merged_file = session.get('merged_file', '')
    file_count = session.get('file_count', 0)
    msg = session.get('merge_msg', '')
    
    return render_template("pdf/merge_pdf.html", 
                         msg=msg,
                         merged_filename=merged_filename,
                         merged_file=merged_file,
                         file_count=file_count)

@merge_pdf_bp.route("/api/upload", methods=["POST"])
def api_upload():
    """API endpoint to upload PDF files"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    uploaded_files = []
    file_info_list = [] # Changed from file_names to store objects
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())[:8]
            unique_filename = f"{unique_id}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            
            file_data = {
                'original_name': filename,
                'unique_name': unique_filename,
                'path': filepath,
                'size': os.path.getsize(filepath)
            }
            uploaded_files.append(file_data)
            
            # Send both original and unique names to frontend
            file_info_list.append({
                'original_name': filename,
                'unique_name': unique_filename
            })
    
    if not uploaded_files:
        return jsonify({'error': 'No valid PDF files uploaded'}), 400
    
    # Store in session (APPEND to existing files instead of overwriting)
    existing_files = session.get('uploaded_files', [])
    existing_files.extend(uploaded_files)
    session['uploaded_files'] = existing_files
    session['file_count'] = len(existing_files)
    
    return jsonify({
        'success': True,
        'files': file_info_list, # Return objects instead of just strings
        'count': len(uploaded_files),
        'message': f'Successfully uploaded {len(uploaded_files)} PDF file(s)'
    })

@merge_pdf_bp.route("/api/remove", methods=["POST"])
def api_remove():
    """API endpoint to remove a single file"""
    data = request.get_json() or {}
    unique_name = data.get('unique_name')
    
    if not unique_name:
        return jsonify({'error': 'No file specified'}), 400
        
    uploaded_files = session.get('uploaded_files', [])
    updated_files = []
    
    for f in uploaded_files:
        if f['unique_name'] == unique_name:
            # Delete the physical file
            if os.path.exists(f['path']):
                try:
                    os.remove(f['path'])
                except Exception:
                    pass
        else:
            updated_files.append(f)
            
    session['uploaded_files'] = updated_files
    session['file_count'] = len(updated_files)
    
    return jsonify({'success': True, 'count': len(updated_files)})

@merge_pdf_bp.route("/api/merge", methods=["POST"])
def api_merge():
    """API endpoint to merge PDF files"""
    data = request.get_json() or {}
    ordered_unique_names = data.get('order', []) # Get custom order from frontend
    uploaded_files = session.get('uploaded_files', [])
    
    if not uploaded_files:
        return jsonify({'error': 'No files to merge'}), 400
    
    if len(uploaded_files) < 2:
        return jsonify({'error': 'Please upload at least 2 PDF files to merge'}), 400
    
    # Reorder files if a custom order is provided
    if ordered_unique_names:
        file_map = {f['unique_name']: f for f in uploaded_files}
        ordered_session_files = []
        
        # Add files in the exact order requested
        for name in ordered_unique_names:
            if name in file_map:
                ordered_session_files.append(file_map[name])
                
        # Fallback: Append any files that weren't in the order list (just in case)
        for f in uploaded_files:
            if f not in ordered_session_files:
                ordered_session_files.append(f)
                
        uploaded_files = ordered_session_files

    try:
        # Create merger
        merger = PdfMerger()
        file_paths = []
        
        # Add all files to merger (now in the correct custom order)
        for file_info in uploaded_files:
            filepath = file_info['path']
            if os.path.exists(filepath):
                merger.append(filepath)
                file_paths.append(filepath)
        
        # Save merged PDF
        unique_id = str(uuid.uuid4())[:8]
        merged_filename = f"merged_{unique_id}.pdf"
        merged_path = os.path.join(UPLOAD_FOLDER, merged_filename)
        merger.write(merged_path)
        merger.close()
        
        # Clean up individual files
        for filepath in file_paths:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass
        
        # Store merged file info in session
        session['merged_filename'] = merged_filename
        session['merged_file'] = merged_path
        session['merge_msg'] = f"✅ Successfully merged {len(uploaded_files)} PDF files!"
        
        # Clear uploaded files from session
        session.pop('uploaded_files', None)
        
        return jsonify({
            'success': True,
            'filename': merged_filename,
            'count': len(uploaded_files),
            'message': f'Successfully merged {len(uploaded_files)} PDF files!'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error merging PDFs: {str(e)}'}), 500

@merge_pdf_bp.route("/api/download", methods=["POST"])
def api_download():
    """API endpoint to get download URL without page reload"""
    merged_file = session.get('merged_file')
    merged_filename = session.get('merged_filename')
    
    if not merged_file or not os.path.exists(merged_file):
        return jsonify({'error': 'No merged PDF to download'}), 404
    
    return jsonify({
        'success': True,
        'url': url_for('merge_pdf.download_merged', _external=True)
    })

@merge_pdf_bp.route("/download")
def download_merged():
    """Download the merged PDF"""
    merged_file = session.get('merged_file')
    merged_filename = session.get('merged_filename')
    
    if not merged_file or not os.path.exists(merged_file):
        return jsonify({'error': 'No merged PDF to download'}), 404
    
    return send_file(merged_file, 
                    as_attachment=True, 
                    download_name=merged_filename or 'merged.pdf')

@merge_pdf_bp.route("/api/clear", methods=["POST"])
def api_clear():
    """API endpoint to clear all data"""
    # Clean up files
    uploaded_files = session.get('uploaded_files', [])
    for file_info in uploaded_files:
        filepath = file_info.get('path')
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
    
    merged_file = session.get('merged_file')
    if merged_file and os.path.exists(merged_file):
        try:
            os.remove(merged_file)
        except:
            pass
    
    # Clear session
    session.pop('uploaded_files', None)
    session.pop('merged_filename', None)
    session.pop('merged_file', None)
    session.pop('file_count', None)
    session.pop('merge_msg', None)
    
    return jsonify({'status': 'success', 'message': 'Cleared successfully'})

@merge_pdf_bp.route("/api/status")
def api_status():
    """API endpoint to check current status"""
    uploaded_files = session.get('uploaded_files', [])
    merged_file = session.get('merged_file')
    
    return jsonify({
        'has_uploaded': len(uploaded_files) > 0,
        'uploaded_count': len(uploaded_files),
        'has_merged': bool(merged_file and os.path.exists(merged_file)),
        'merged_filename': session.get('merged_filename', '')
    })