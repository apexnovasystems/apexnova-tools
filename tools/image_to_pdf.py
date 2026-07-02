from flask import Blueprint, request, render_template, send_file, after_this_request
import img2pdf
import io
from PIL import Image

image_to_pdf_bp = Blueprint("image_to_pdf", __name__)

def get_layout_fun(page_size, quality):
    """Return layout function for img2pdf based on page size."""
    if page_size == 'a4':
        pagesize = img2pdf.pagesize.A4
    elif page_size == 'letter':
        pagesize = img2pdf.pagesize.LETTER
    else:
        pagesize = None

    # FitMode (capital M) is correct
    if pagesize is None:
        return img2pdf.get_layout_fun(fit=img2pdf.FitMode.into)
    else:
        return img2pdf.get_layout_fun(pagesize=pagesize, fit=img2pdf.FitMode.into)

@image_to_pdf_bp.route("/", methods=["GET", "POST"])
def index():
    msg = ""  # ✅ define for GET
    if request.method == "POST":
        uploaded_files = request.files.getlist("images")
        if not uploaded_files:
            return render_template("pdf/image_to_pdf.html", msg="No images selected.")
        
        quality = request.form.get("quality", "medium")
        page_size = request.form.get("page_size", "auto")
        
        image_bytes_list = []
        for f in uploaded_files:
            if f and f.filename:
                img_bytes = f.read()
                try:
                    Image.open(io.BytesIO(img_bytes)).verify()
                    image_bytes_list.append(img_bytes)
                except Exception:
                    continue
        
        if not image_bytes_list:
            return render_template("pdf/image_to_pdf.html", msg="No valid images found.")
        
        layout_fun = get_layout_fun(page_size, quality)
        
        try:
            pdf_bytes = img2pdf.convert(image_bytes_list, layout_fun=layout_fun)
        except Exception as e:
            return render_template("pdf/image_to_pdf.html", msg=f"Conversion error: {str(e)}")
        
        @after_this_request
        def cleanup(response):
            return response
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='converted.pdf'
        )
    
    # GET request
    return render_template("pdf/image_to_pdf.html", msg=msg)


@image_to_pdf_bp.route("/cleanup", methods=["POST"])
def cleanup():
    # No disk files to delete, but we keep session clean
    return "", 204