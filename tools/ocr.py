from flask import Blueprint, request, render_template, flash, redirect, url_for, session, jsonify
from PIL import Image
import pytesseract
import os
import uuid
import shutil
from werkzeug.utils import secure_filename

ocr_bp = Blueprint("ocr", __name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_session():
    """Clean up session data"""
    session.pop('ocr_text', None)
    session.pop('ocr_msg', None)
    session.pop('ocr_file', None)
    session.pop('ocr_processed', None)
    session.pop('ocr_cleared', None)

@ocr_bp.route("/", methods=["GET"])
def index_get():
    """Handle GET requests - show the form with any existing session data"""
    
    # Check if clear parameter is present
    clear = request.args.get('clear', 'false').lower() == 'true'
    
    if clear:
        # Clear all session data
        cleanup_session()
        # Set a flag to indicate we've cleared
        session['ocr_cleared'] = True
        # Render with empty data
        return render_template("ocr.html", text="", msg=None)
    
    # Check if we have a cleared flag
    if session.get('ocr_cleared'):
        # If we've cleared, don't show data
        session.pop('ocr_cleared', None)
        return render_template("ocr.html", text="", msg=None)
    
    # Get data from session
    text = session.get('ocr_text', '')
    msg = session.get('ocr_msg', '')
    
    # If there's text but no msg, create a default message
    if text and not msg:
        word_count = len(text.split())
        msg = f"✅ Successfully extracted {word_count} words from the image."
    
    return render_template("ocr.html", text=text, msg=msg)

@ocr_bp.route("/", methods=["POST"])
def index_post():
    """Handle POST requests - process the image and redirect to GET"""
    text = ""
    msg = None
    filename = None
    
    # Clear any previous cleared flag
    session.pop('ocr_cleared', None)
    
    # Check if file was uploaded
    if 'file' not in request.files:
        msg = "No file selected. Please upload an image."
        session['ocr_msg'] = msg
        session['ocr_processed'] = True
        return redirect(url_for('ocr.index_get'))
    
    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        msg = "No file selected. Please upload an image."
        session['ocr_msg'] = msg
        session['ocr_processed'] = True
        return redirect(url_for('ocr.index_get'))
    
    # Check file extension
    if not allowed_file(file.filename):
        msg = "Invalid file type. Please upload JPG, PNG, WEBP, BMP, or TIFF."
        session['ocr_msg'] = msg
        session['ocr_processed'] = True
        return redirect(url_for('ocr.index_get'))
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        msg = f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB."
        session['ocr_msg'] = msg
        session['ocr_processed'] = True
        return redirect(url_for('ocr.index_get'))
    
    try:
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{unique_id}_{original_filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        file.save(filepath)
        
        # Open image with PIL
        image = Image.open(filepath)
        
        # Preprocess image for better OCR results
        if image.mode not in ('L', 'RGB'):
            image = image.convert('RGB')
        
        # Perform OCR with multiple language support
        text = pytesseract.image_to_string(
            image, 
            lang='eng',
            config='--psm 6 --oem 3'
        )
        
        # Clean up text
        text = text.strip()
        
        if not text:
            msg = "No text could be extracted from the image. Please try with a clearer image."
        else:
            word_count = len(text.split())
            msg = f"✅ Successfully extracted {word_count} words from the image."
            
            # Store in session for persistence
            session['ocr_text'] = text
            session['ocr_msg'] = msg
            session['ocr_file'] = filename
        
        # Clean up file after processing
        if os.path.exists(filepath):
            os.remove(filepath)
        
    except Exception as e:
        msg = f"Error processing image: {str(e)}"
        # Clean up if file was saved
        if filename and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
    
    # Set processed flag and redirect to GET
    session['ocr_processed'] = True
    return redirect(url_for('ocr.index_get'))

@ocr_bp.route("/clear")
def clear():
    """Clear all session data and redirect"""
    cleanup_session()
    session['ocr_cleared'] = True
    return redirect(url_for('ocr.index_get', clear='true'))

@ocr_bp.route("/api/clear", methods=["POST"])
def api_clear():
    """API endpoint to clear everything from server"""
    try:
        cleanup_session()
        session['ocr_cleared'] = True
        return jsonify({
            'status': 'success', 
            'message': 'All data cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

@ocr_bp.route("/api/clear-text", methods=["POST"])
def api_clear_text():
    """API endpoint to clear only text from session"""
    try:
        session.pop('ocr_text', None)
        session.pop('ocr_msg', None)
        session['ocr_cleared'] = True
        return jsonify({
            'status': 'success', 
            'message': 'Text cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

@ocr_bp.route("/api/status")
def api_status():
    """API endpoint to check if there's data"""
    has_text = 'ocr_text' in session and session['ocr_text']
    return jsonify({
        'has_text': bool(has_text),
        'word_count': len(session.get('ocr_text', '').split()) if has_text else 0,
        'has_file': 'ocr_file' in session,
        'cleared': session.get('ocr_cleared', False)
    })

@ocr_bp.route("/download-text")
def download_text():
    """Download extracted text as .txt file"""
    text = request.args.get('text', '')
    if not text:
        # Try to get from session
        text = session.get('ocr_text', '')
    
    if not text:
        flash('No text to download', 'error')
        return redirect(url_for('ocr.index_get'))
    
    # Create a text file
    from flask import make_response
    
    response = make_response(text)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=extracted_text_{uuid.uuid4().hex[:8]}.txt'
    return response