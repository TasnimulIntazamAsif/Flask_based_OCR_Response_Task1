# OCR API (EasyOCR + Tesseract + PaddleOCR)

A Flask-based OCR API that processes images (such as **Visiting Cards** and **Passports**) using **three OCR engines**—EasyOCR, Tesseract, and PaddleOCR.  
The API cleans OCR text and extracts structured information like emails, phone numbers, addresses, passport numbers, dates of birth, and MRZ codes.

It also includes **Swagger UI** for easy testing and documentation.
After running the main.py app there will a hyperlink . by clickinf on the link it will take away to the webpage . then we need to give http://127.0.0.1:5000/swagger. then the app will be open for the text extraction from id card/visitng card/passport id images

---

## 🚀 Features

- Multi-OCR support:
  - EasyOCR
  - Tesseract OCR
  - PaddleOCR
- Regex-based text cleaning
- Structured information extraction:
  - Emails
  - Phone numbers
  - Addresses
  - Passport numbers
  - Date of birth
  - MRZ (Machine Readable Zone)
- Combined OCR result for improved accuracy
- Swagger UI for API testing
- CORS enabled (frontend-friendly)
- Temporary image storage (auto-deleted after processing)

---

## 🛠️ Tech Stack

- **Backend:** Flask
- **OCR Engines:** EasyOCR, Tesseract, PaddleOCR
- **Image Processing:** OpenCV
- **API Documentation:** Flasgger (Swagger)
- **Language:** Python 3.x

---

## 📦 Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/ocr-api.git
cd ocr-api
