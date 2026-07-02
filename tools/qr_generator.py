from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify, send_file
import qrcode
import os
import uuid
from io import BytesIO
import base64

qr_bp = Blueprint("qr", __name__)

# Configuration
OUTPUT_FOLDER = 'static/qr_codes'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@qr_bp.route("/", methods=["GET"])
def index_get():
    """Handle GET requests - show the form with any existing QR data"""
    qr_data = session.get('qr_data', '')
    qr_image = session.get('qr_image', '')
    msg = session.get('qr_msg', '')
    
    return render_template("qr_generator.html", 
                         msg=msg, 
                         qr_data=qr_data,
                         qr_image=qr_image)

@qr_bp.route("/", methods=["POST"])
def index_post():
    """Handle POST requests - generate QR code and redirect to GET"""
    text = request.form.get("text", "").strip()
    
    if not text:
        session['qr_msg'] = "Please enter some text or URL to generate a QR code."
        session['qr_data'] = ''
        session['qr_image'] = ''
        return redirect(url_for('qr.index_get'))
    
    try:
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO for base64 encoding
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Store in session
        session['qr_data'] = text
        session['qr_image'] = img_str
        session['qr_msg'] = f"✅ QR Code generated successfully for: {text[:50]}{'...' if len(text) > 50 else ''}"
        
        # Also save to file for download
        unique_id = str(uuid.uuid4())[:8]
        filename = f"qr_{unique_id}.png"
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        img.save(filepath)
        session['qr_filename'] = filename
        
    except Exception as e:
        session['qr_msg'] = f"Error generating QR code: {str(e)}"
    
    return redirect(url_for('qr.index_get'))

@qr_bp.route("/api/generate", methods=["POST"])
def api_generate():
    """API endpoint to generate QR code without page reload"""
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Store in session for download
        unique_id = str(uuid.uuid4())[:8]
        filename = f"qr_{unique_id}.png"
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        img.save(filepath)
        session['qr_filename'] = filename
        session['qr_data'] = text
        session['qr_image'] = img_str
        
        return jsonify({
            'success': True,
            'image': img_str,
            'data': text,
            'message': f"QR Code generated successfully for: {text[:50]}{'...' if len(text) > 50 else ''}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_bp.route("/api/clear", methods=["POST"])
def api_clear():
    """API endpoint to clear QR data"""
    session.pop('qr_data', None)
    session.pop('qr_image', None)
    session.pop('qr_msg', None)
    session.pop('qr_filename', None)
    return jsonify({'status': 'success', 'message': 'Cleared successfully'})

@qr_bp.route("/api/download", methods=["POST"])
def api_download():
    """API endpoint to get download URL without page reload"""
    filename = session.get('qr_filename')
    if not filename:
        return jsonify({'error': 'No QR code to download'}), 404
    
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'QR code file not found'}), 404
    
    return jsonify({
        'success': True,
        'url': url_for('qr.download_qr', _external=True)
    })

@qr_bp.route("/download")
def download_qr():
    """Download the generated QR code as PNG"""
    filename = session.get('qr_filename')
    if not filename:
        return jsonify({'error': 'No QR code to download'}), 404
    
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'QR code file not found'}), 404
    
    return send_file(filepath, as_attachment=True, download_name='qr_code.png')

@qr_bp.route("/clear")
def clear():
    """Clear QR data and redirect"""
    session.pop('qr_data', None)
    session.pop('qr_image', None)
    session.pop('qr_msg', None)
    session.pop('qr_filename', None)
    return redirect(url_for('qr.index_get'))