import traceback
import secrets
import os

from flask import Flask, render_template, jsonify, request

# Blueprints
from tools.pdf_to_image import pdf_to_image_bp
from tools.image_to_pdf import image_to_pdf_bp
from tools.qr_generator import qr_bp
from tools.ocr import ocr_bp
from tools.merge_pdf import merge_pdf_bp

from werkzeug.middleware.proxy_fix import ProxyFix

# =========================
# APP INIT (IMPORTANT)
# =========================

app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static",
    subdomain_matching=True
)

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_port=1
)



# =========================
# CONFIG
# =========================
app.config["SERVER_NAME"] = "apexnovasystems.tech"  # 🔥 REQUIRED for subdomains
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=3600
)


# =========================
# SUBDOMAIN ROUTES
# =========================


# MAIN HOMEPAGE
@app.route("/", subdomain="tools")
def tools_home():
    return render_template("index.html")



# =========================
# BLUEPRINTS (API ROUTES)
# =========================
# 🔥 Register the PDF to Image blueprint specifically for the 'pdftoimage' subdomain
app.register_blueprint(pdf_to_image_bp, subdomain="pdftoimage")

app.register_blueprint(image_to_pdf_bp, subdomain="imagetopdf")
app.register_blueprint(qr_bp, subdomain="qr")
app.register_blueprint(ocr_bp, subdomain="ocr")
app.register_blueprint(merge_pdf_bp, subdomain='mergepdf')


# =========================
# ERROR HANDLERS
# =========================
@app.errorhandler(413)
def file_too_large(e):
    return jsonify({
        "error": "File too large",
        "message": "Maximum file size is 50MB",
        "status": 413
    }), 413


@app.errorhandler(404)
def not_found(e):
    trace = traceback.format_exc()
    app.logger.error(
        f"404 | {request.method} | {request.url}\n{repr(e)}\n{trace}"
    )

    return jsonify({
        "error": "Not Found",
        "message": "The requested URL was not found on the server.",
        "status": 404
    }), 404


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )