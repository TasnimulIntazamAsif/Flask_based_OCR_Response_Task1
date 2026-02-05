from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
import easyocr
import pytesseract
import cv2
import os
import re

# ------------------ Paddle safety ------------------
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

from paddleocr import PaddleOCR

# ------------------ Flask App ------------------
app = Flask(__name__)
CORS(app)

# ✅ FIXED Swagger config (specs added)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/",
    "title": "OCR API",
    "description": "OCR using EasyOCR, Tesseract, and PaddleOCR",
    "version": "1.0.0"
}

Swagger(app, config=swagger_config)

# ------------------ OCR Engines ------------------
easy_reader = easyocr.Reader(['en'])
paddle_ocr = PaddleOCR(use_textline_orientation=True, lang='en')

# ------------------ OCR FUNCTIONS ------------------
def ocr_with_tesseract(image_path):
    try:
        image = cv2.imread(image_path)
        return pytesseract.image_to_string(image)
    except Exception:
        return ""

def ocr_with_paddle(image_path):
    try:
        result = paddle_ocr.ocr(image_path, cls=True)

        texts = []

        # PaddleOCR output format varies by version
        for item in result:
            if isinstance(item, list):
                for line in item:
                    if len(line) >= 2 and isinstance(line[1], (list, tuple)):
                        texts.append(str(line[1][0]))
            elif isinstance(item, tuple) and len(item) >= 2:
                texts.append(str(item[1][0]))

        return "\n".join(texts)

    except Exception as e:
        print("PaddleOCR error:", e)
        return ""


# ------------------ REGEX CLEAN ------------------
def clean_text_regex(text):
    if not text:
        return ""
    text = re.sub(r"[^A-Za-z0-9\s\.\,\-\(\)\/@:+<]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ------------------ EXTRACTORS ------------------
def extract_emails(text):
    return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)))

def extract_phones(text):
    return list(set(re.findall(r"(?:\+880|\+88|01|\+?\d{1,3})[\s\-]?\d{8,11}", text)))

def extract_addresses(text):
    keywords = ["road", "street", "avenue", "house", "floor", "block", "dhaka", "bangladesh"]
    lines = re.split(r"[,.]", text)
    return [l.strip() for l in lines if any(k in l.lower() for k in keywords)]

def extract_passport_number(text):
    return list(set(re.findall(r"\b[A-Z]{1,2}[0-9]{7,8}\b", text)))

def extract_dob(text):
    return list(set(re.findall(r"\b\d{2}[\/\-]\d{2}[\/\-]\d{4}\b", text)))

def extract_mrz(text):
    return list(set(re.findall(r"P[A-Z<]{20,44}", text)))

def extract_all(text):
    return {
        "visiting_card": {
            "emails": extract_emails(text),
            "phones": extract_phones(text),
            "addresses": extract_addresses(text)
        },
        "passport": {
            "passport_numbers": extract_passport_number(text),
            "date_of_birth": extract_dob(text),
            "mrz": extract_mrz(text)
        }
    }

# ------------------ HOME (GET) ------------------
@app.route('/', methods=['GET'])
def home():
    """
    API Health Check
    ---
    tags:
      - Health
    responses:
      200:
        description: API is running
    """
    return jsonify({
        "message": "OCR API running (EasyOCR + Tesseract + PaddleOCR)"
    })

# ------------------ PROCESS (POST) ------------------
@app.route('/process', methods=['POST'])
def process_document():
    """
    Process Image with 3 OCR Engines
    ---
    tags:
      - OCR
    consumes:
      - multipart/form-data
    parameters:
      - name: image
        in: formData
        type: file
        required: true
        description: Image for OCR (Visiting Card / Passport)
    responses:
      200:
        description: OCR result from all engines
    """
    image_file = request.files.get('image')
    if not image_file:
        return jsonify({"error": "Image is required"}), 400

    os.makedirs("uploads", exist_ok=True)
    image_path = os.path.join("uploads", image_file.filename)
    image_file.save(image_path)

    # ---- OCR ----
    easy_raw = "\n".join([t[1] for t in easy_reader.readtext(image_path)])
    tess_raw = ocr_with_tesseract(image_path)
    paddle_raw = ocr_with_paddle(image_path)

    # ---- CLEAN ----
    easy_clean = clean_text_regex(easy_raw)
    tess_clean = clean_text_regex(tess_raw)
    paddle_clean = clean_text_regex(paddle_raw)

    combined_text = clean_text_regex(
        f"{easy_clean} {tess_clean} {paddle_clean}"
    )

    os.remove(image_path)

    return jsonify({
        "ocr_results": {
            "easyocr": {
                "raw": easy_raw,
                "cleaned": easy_clean,
                "extracted": extract_all(easy_clean)
            },
            "tesseract": {
                "raw": tess_raw,
                "cleaned": tess_clean,
                "extracted": extract_all(tess_clean)
            },
            "paddleocr": {
                "raw": paddle_raw,
                "cleaned": paddle_clean,
                "extracted": extract_all(paddle_clean)
            }
        },
        "combined_result": {
            "cleaned_text": combined_text,
            "extracted": extract_all(combined_text)
        }
    })

# ------------------ Run ------------------
if __name__ == '__main__':
    app.run(debug=True)
