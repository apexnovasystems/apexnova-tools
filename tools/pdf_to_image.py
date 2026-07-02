import uuid
import shutil
import zipfile
from pathlib import Path
from flask import Blueprint, request,render_template, jsonify, send_file, abort, after_this_request, url_for
from pdf2image import convert_from_path

pdf_to_image_bp = Blueprint("pdf_to_image", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent / "static/storage/pdf_converter"
BASE_DIR.mkdir(parents=True, exist_ok=True)

def delete_job_folder(job_id: str):
    folder = BASE_DIR / job_id
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)

def get_dpi(quality: str) -> int:
    return {"high": 300, "medium": 150, "low": 72}.get(quality, 150)

@pdf_to_image_bp.route("/", methods=["POST"])
def convert_pdf():
    job_id = request.form.get("job_id")
    if not job_id:
        return jsonify({"success": False, "error": "Missing job_id"}), 400

    file = request.files.get("file")
    if not file or not file.filename.endswith(".pdf"):
        return jsonify({"success": False, "error": "Please provide a valid PDF file"}), 400

    quality = request.form.get("quality", "medium")
    img_format = request.form.get("format", "png").lower()
    if img_format not in ("png", "jpeg"):
        img_format = "png"

    dpi = get_dpi(quality)
    ext = "png" if img_format == "png" else "jpg"

    job_dir = BASE_DIR / job_id
    upload_dir = job_dir / "upload"
    output_dir = job_dir / "output"
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Clean previous output
    for f in output_dir.glob("*"):
        f.unlink()

    pdf_path = upload_dir / "input.pdf"
    file.save(str(pdf_path))

    try:
        pages = convert_from_path(str(pdf_path), dpi=dpi)
    except Exception as e:
        return jsonify({"success": False, "error": f"PDF conversion failed: {str(e)}"}), 500

    image_urls = []
    for i, page in enumerate(pages, start=1):
        filename = f"page_{i}.{ext}"
        out_path = output_dir / filename
        if img_format == "png":
            page.save(out_path, "PNG")
        else:
            if page.mode != "RGB":
                page = page.convert("RGB")
            page.save(out_path, "JPEG", quality=85)
        image_urls.append({
            "index": i,
            "url": url_for("pdf_to_image.serve_image", job_id=job_id, page=i, _external=False)
        })

    (job_dir / "format.txt").write_text(img_format)

    return jsonify({
        "success": True,
        "message": f"{len(pages)} pages converted successfully",
        "job_id": job_id,
        "images": image_urls
    })

@pdf_to_image_bp.route("/file/<job_id>/<int:page>")
def serve_image(job_id, page):
    job_dir = BASE_DIR / job_id
    if not job_dir.exists():
        abort(404, description="Job not found")
    fmt_file = job_dir / "format.txt"
    img_format = fmt_file.read_text().strip() if fmt_file.exists() else "png"
    ext = "png" if img_format == "png" else "jpg"
    file_path = job_dir / "output" / f"page_{page}.{ext}"
    if not file_path.exists():
        abort(404, description="Image not found")
    mimetype = "image/png" if ext == "png" else "image/jpeg"
    return send_file(file_path, mimetype=mimetype)

@pdf_to_image_bp.route("/download-zip")
def download_zip():
    job_id = request.args.get("job_id")
    if not job_id:
        abort(400, description="Missing job_id")
    job_dir = BASE_DIR / job_id
    output_dir = job_dir / "output"
    if not output_dir.exists() or not any(output_dir.glob("*")):
        abort(404, description="No images found")
    zip_path = job_dir / "images.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for f in output_dir.glob("*"):
            zipf.write(f, arcname=f.name)
    @after_this_request
    def remove_zip(response):
        try:
            zip_path.unlink()
        except Exception:
            pass
        return response
    return send_file(zip_path, as_attachment=True, download_name="images.zip")

@pdf_to_image_bp.route("/cleanup", methods=["POST"])
def cleanup():
    job_id = request.form.get("job_id") or request.args.get("job_id")
    if not job_id:
        return jsonify({"success": False, "error": "Missing job_id"}), 400
    delete_job_folder(job_id)
    return jsonify({"success": True}), 200

@pdf_to_image_bp.route("/list-images", methods=["GET"])
def list_images():
    job_id = request.args.get("job_id")
    if not job_id:
        return jsonify({"success": False, "error": "Missing job_id"}), 400
    output_dir = BASE_DIR / job_id / "output"
    if not output_dir.exists():
        return jsonify({"success": True, "images": []})
    fmt_file = BASE_DIR / job_id / "format.txt"
    img_format = fmt_file.read_text().strip() if fmt_file.exists() else "png"
    ext = "png" if img_format == "png" else "jpg"
    images = []
    for p in sorted(output_dir.glob(f"page_*.{ext}")):
        page_num = int(p.stem.split("_")[1])
        images.append({
            "index": page_num,
            "url": url_for("pdf_to_image.serve_image", job_id=job_id, page=page_num, _external=False)
        })
    return jsonify({"success": True, "images": images})

@pdf_to_image_bp.route("/", methods=["GET"])
def index():
    return render_template("pdf/pdf_to_image.html")