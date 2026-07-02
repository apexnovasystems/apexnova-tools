# ApexNova Tools

A collection of online file conversion and utility tools built with Flask and Docker.

## Features

### PDF Tools

* PDF to Image
* Image to PDF

### Image Tools

* OCR (Image to Text)
* QR Code Generator

### Upcoming Tools

* PDF Merge
* PDF Split
* PDF Compress
* JPG to PNG
* PNG to JPG
* Background Remover
* Image Resizer
* Watermark Tool
* File Compressor
* Text Utilities

---

## Tech Stack

* Python 3.12
* Flask
* Docker
* Gunicorn
* PDF2Image
* Pillow
* Img2PDF
* PyTesseract
* QRCode

---

## Project Structure

```text
apexnova-tools/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│
├── tools/
│   ├── pdf_to_image.py
│   ├── image_to_pdf.py
│   ├── qr_generator.py
│   └── ocr.py
│
├── templates/
│   ├── index.html
│   ├── pdf_to_image.html
│   ├── image_to_pdf.html
│   ├── qr_generator.html
│   └── ocr.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/
│
└── output/
```

---

## Local Installation

Clone the repository:

```bash
git clone https://github.com/apexnovasystems/apexnova-tools.git
cd apexnova-tools
```

Create virtual environment:

```bash
python -m venv venv
```

Activate virtual environment:

Windows

```bash
venv\Scripts\activate
```

Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run application:

```bash
python app.py
```

Application URL:

```text
http://localhost:5000
```

---

## Docker Deployment

Build and run:

```bash
docker compose up -d --build
```

Check running containers:

```bash
docker ps
```

View logs:

```bash
docker logs apexnova_tools
```

---

## VPS Deployment

1. Create a Docker project in Hostinger Docker Manager.
2. Clone the repository on the server.
3. Run:

```bash
docker compose up -d --build
```

4. Configure DNS records.

Example:

```text
tools.yourdomain.com
pdf.yourdomain.com
img2pdf.yourdomain.com
ocr.yourdomain.com
qr.yourdomain.com
```

5. Configure Traefik or Nginx reverse proxy for SSL.

---

## Required Dependencies

### Windows Development

PDF to Image requires Poppler:

https://github.com/oschwartz10612/poppler-windows/releases

OCR requires Tesseract:

https://github.com/UB-Mannheim/tesseract/wiki

### Docker/Linux

Already included in Dockerfile:

```bash
poppler-utils
tesseract-ocr
```

---

## Roadmap

* User Accounts
* API Access
* Batch Processing
* Cloud Storage Integration
* AI Tools
* Image Editing Tools
* Document Conversion Tools
* SEO Tools
* Developer Tools

---

## License

MIT License

---

## Author

ApexNova Systems

Website: https://apexnovasystems.com

GitHub: https://github.com/apexnovasystems
