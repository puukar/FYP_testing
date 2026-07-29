import subprocess
import os
import platform
import tempfile
import shutil
from pathlib import Path
from typing import Optional

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    import pypdfium2 as pdfium
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR libraries not available. Install: pip install pytesseract pdf2image pillow")

class CrossPlatformPDFExtractor:

    def __init__(self):
        self.system = platform.system()
        self.pdftotext_path = self._find_pdftotext()
        self.poppler_path = self._find_poppler()
        self.tesseract_path = self._find_tesseract()

    def _find_pdftotext(self) -> Optional[str]:
        if self.system == "Windows":
            possible_paths = [
                r"C:\poppler\Library\bin\pdftotext.exe",
                r"C:\Program Files\poppler\bin\pdftotext.exe",
                os.path.expanduser(r"~\poppler\bin\pdftotext.exe")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path

        if shutil.which("pdftotext"):
            return "pdftotext"

        return None

    def _find_poppler(self) -> Optional[str]:
        if self.system == "Windows":
            possible_paths = [
                r"C:\poppler\Library\bin",
                r"C:\Program Files\poppler\bin",
                os.path.expanduser(r"~\poppler\bin")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            return None

        return None

    def _find_tesseract(self) -> Optional[str]:
        if not OCR_AVAILABLE:
            return None

        if self.system == "Windows":
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    return path

        if shutil.which("tesseract"):
            return "tesseract"

        return None

    def extract_text(self, pdf_path: str) -> Optional[str]:

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        print(f"🔍 Extracting from: {path.name}")
        print(f"📊 File size: {path.stat().st_size} bytes")
        print(f"💻 System: {self.system}")

        text = self._try_pdftotext(pdf_path)
        if text and text.strip():
            print(f"✅ pdftotext extracted: {len(text)} characters")
            return text

        text = self._try_pypdf2(pdf_path)
        if text and text.strip():
            print(f"✅ PyPDF2 extracted: {len(text)} characters")
            return text

        text = self._try_pdfplumber(pdf_path)
        if text and text.strip():
            print(f"✅ pdfplumber extracted: {len(text)} characters")
            return text

        if OCR_AVAILABLE and self.tesseract_path:
            print("🔄 Trying OCR...")
            text = self._try_ocr(pdf_path)
            if text and text.strip():
                print(f"✅ OCR extracted: {len(text)} characters")
                return text

        print("❌ All extraction methods failed")
        return None

    def _try_pdftotext(self, pdf_path: str) -> Optional[str]:
        """Extract using pdftotext command"""
        if not self.pdftotext_path:
            return None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
                temp_path = temp_file.name

            cmd = [self.pdftotext_path, "-layout", "-enc", "UTF-8", str(pdf_path), temp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and os.path.exists(temp_path):
                with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                os.unlink(temp_path)
                return text

        except Exception as e:
            print(f"⚠️ pdftotext failed: {e}")

        return None

    def _try_pypdf2(self, pdf_path: str) -> Optional[str]:
        """Extract using PyPDF2"""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"⚠️ PyPDF2 failed: {e}")
            return None

    def _try_pdfplumber(self, pdf_path: str) -> Optional[str]:
        """Extract using pdfplumber"""
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            print(f"⚠️ pdfplumber failed: {e}")
            return None

    def _try_ocr(self, pdf_path: str) -> Optional[str]:
        """Extract using OCR"""
        if not OCR_AVAILABLE or not self.tesseract_path:
            return None

        try:
            images = self._render_pdf_images(pdf_path)
            if not images:
                return None

            text = ""
            for i, image in enumerate(images):
                print(f"🔍 OCR processing page {i+1}/{len(images)}...")
                page_text = pytesseract.image_to_string(image, config='--psm 6')
                if page_text.strip():
                    text += f"--- Page {i+1} ---\n{page_text}\n"

            return text if text.strip() else None

        except Exception as e:
            print(f"❌ OCR failed: {e}")
            return None

    def _render_pdf_images(self, pdf_path: str):
        """Render PDF pages to PIL images for OCR."""
        if self.poppler_path:
            try:
                return convert_from_path(
                    pdf_path,
                    dpi=200,
                    poppler_path=self.poppler_path
                )
            except Exception as e:
                print(f"âš ï¸ pdf2image rendering failed: {e}")

        try:
            pdf = pdfium.PdfDocument(pdf_path)
            images = []
            for page_index in range(len(pdf)):
                page = pdf[page_index]
                bitmap = page.render(scale=200 / 72)
                images.append(bitmap.to_pil())
            return images
        except Exception as e:
            print(f"âš ï¸ pypdfium2 rendering failed: {e}")
            return None

pdf_extractor = CrossPlatformPDFExtractor()

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Main extraction function"""
    return pdf_extractor.extract_text(pdf_path)
