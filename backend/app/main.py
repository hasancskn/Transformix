from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import shutil
import subprocess
from pathlib import Path
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
import io
import os
import logging

logger = logging.getLogger("transformix")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Transformix API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Capability(BaseModel):
    name: str
    from_type: str
    to_type: str
    endpoint: str


CAPABILITIES: List[Capability] = [
    Capability(name="Word to PDF", from_type="docx|doc", to_type="pdf", endpoint="/convert/word-to-pdf"),
    Capability(name="PDF to Word", from_type="pdf", to_type="docx", endpoint="/convert/pdf-to-word"),
    Capability(name="PDF to JPG", from_type="pdf", to_type="jpg", endpoint="/convert/pdf-to-jpg"),
    Capability(name="JPG to PDF", from_type="jpg|jpeg|png", to_type="pdf", endpoint="/convert/jpg-to-pdf"),
    Capability(name="Compress PDF", from_type="pdf", to_type="pdf", endpoint="/compress/pdf"),
    Capability(name="Merge PDF", from_type="pdf[]", to_type="pdf", endpoint="/pdf/merge"),
    Capability(name="Split PDF", from_type="pdf", to_type="pdf[]", endpoint="/pdf/split"),
    Capability(name="Rotate PDF", from_type="pdf", to_type="pdf", endpoint="/pdf/rotate"),
    Capability(name="Protect PDF", from_type="pdf", to_type="pdf", endpoint="/pdf/protect"),
    Capability(name="HTML to PDF", from_type="html|url", to_type="pdf", endpoint="/convert/html-to-pdf"),
]


@app.get("/")
async def list_capabilities():
    return JSONResponse([c.model_dump() for c in CAPABILITIES])


# Helpers

def _tmp_path(suffix: str) -> Path:
    return Path(tempfile.mkstemp(suffix=suffix)[1])


def _stream_file(path: Path, media_type: str, filename: Optional[str] = None):
    # Read file into memory before TemporaryDirectory cleanup to avoid broken pipe
    data = path.read_bytes()
    headers = {
        "Content-Disposition": f"attachment; filename={filename or path.name}",
    }
    return Response(content=data, media_type=media_type, headers=headers)


# Conversions

@app.post("/convert/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    # Use LibreOffice headless conversion
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / file.filename
        output_dir = Path(tmpdir)
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        try:
            result = subprocess.run([
                "soffice", "--headless", "--convert-to", "pdf:writer_pdf_Export", "--outdir", str(output_dir), str(input_path)
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise HTTPException(400, detail=f"Conversion failed: {e.stderr.decode(errors='ignore')[:500]}")
        # Expected path by stem
        out_pdf = output_dir / (input_path.stem + ".pdf")
        if not out_pdf.exists():
            # Fallback: pick any single generated PDF
            pdfs = list(output_dir.glob("*.pdf"))
            if len(pdfs) == 1:
                out_pdf = pdfs[0]
        if not out_pdf.exists():
            stdcombined = (result.stdout or b'') + b"\n" + (result.stderr or b'')
            raise HTTPException(500, detail=f"Converted file not found. Logs: {stdcombined.decode(errors='ignore')[:500]}")
        return _stream_file(out_pdf, "application/pdf", filename=out_pdf.name)


@app.post("/convert/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    # Convert PDF to DOCX using pdf2docx (no LibreOffice needed)
    from pdf2docx import Converter
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / file.filename
        output_path = Path(tmpdir) / (Path(file.filename).stem + ".docx")
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        try:
            cv = Converter(str(input_path))
            cv.convert(str(output_path), start=0, end=None)
            cv.close()
        except Exception as e:
            raise HTTPException(400, detail=f"pdf2docx failed: {e}")
        if not output_path.exists():
            raise HTTPException(500, detail="Converted file not found")
        return _stream_file(output_path, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=output_path.name)


@app.post("/convert/pdf-to-jpg")
async def pdf_to_jpg(file: UploadFile = File(...)):
    # Convert each page to JPG using pdftoppm (Poppler)
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / file.filename
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        try:
            # Produces files like page-1.jpg, page-2.jpg ...
            subprocess.run([
                "pdftoppm", "-jpeg", "-r", "150", str(input_path), str(Path(tmpdir) / "page")
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise HTTPException(400, detail=f"pdftoppm failed: {e.stderr.decode(errors='ignore')[:500]}")
        # Zip results
        import zipfile
        zip_path = Path(tmpdir) / f"{input_path.stem}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for img in sorted(Path(tmpdir).glob("page-*.jpg")):
                zf.write(img, arcname=img.name)
        return _stream_file(zip_path, "application/zip", filename=zip_path.name)


@app.post("/convert/jpg-to-pdf")
async def jpg_to_pdf(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    out_path = _tmp_path(".pdf")
    image.save(out_path, "PDF")
    return _stream_file(out_path, "application/pdf", filename=f"{Path(file.filename).stem}.pdf")


@app.post("/compress/pdf")
async def compress_pdf(file: UploadFile = File(...), quality: int = Form(85)):
    # Use ghostscript for compression
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / file.filename
        output_path = Path(tmpdir) / f"compressed_{Path(file.filename).stem}.pdf"
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        try:
            subprocess.run([
                "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
                "-dPDFSETTINGS=/ebook", f"-dJPEGQ={quality}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
                f"-sOutputFile={output_path}", str(input_path)
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise HTTPException(400, detail=f"Compression failed: {e.stderr.decode(errors='ignore')[:500]}")
        return _stream_file(output_path, "application/pdf", filename=output_path.name)


@app.post("/pdf/merge")
async def merge_pdf(files: List[UploadFile] = File(...)):
    logger.info("/pdf/merge called with %s files", len(files))
    merger = PdfMerger()
    with tempfile.TemporaryDirectory() as tmpdir:
        for f in files:
            path = Path(tmpdir) / f.filename
            with open(path, "wb") as out:
                shutil.copyfileobj(f.file, out)
            merger.append(str(path))
        merged_path = Path(tmpdir) / "merged.pdf"
        with open(merged_path, "wb") as out:
            merger.write(out)
        merger.close()
        logger.info("/pdf/merge produced %s bytes", merged_path.stat().st_size)
        return _stream_file(merged_path, "application/pdf", filename="merged.pdf")


@app.post("/pdf/split")
async def split_pdf(file: UploadFile = File(...), from_page: int = Form(1), to_page: Optional[int] = Form(None)):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / file.filename
        with open(input_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        reader = PdfReader(str(input_path))
        if to_page is None:
            to_page = len(reader.pages)
        writer = PdfWriter()
        for i in range(from_page - 1, to_page):
            writer.add_page(reader.pages[i])
        output = Path(tmpdir) / f"split_{from_page}_{to_page}.pdf"
        with open(output, "wb") as f:
            writer.write(f)
        return _stream_file(output, "application/pdf", filename=output.name)


@app.post("/pdf/rotate")
async def rotate_pdf(file: UploadFile = File(...), degrees: int = Form(90)):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / file.filename
        with open(input_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        reader = PdfReader(str(input_path))
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(degrees)
            writer.add_page(page)
        rotated = Path(tmpdir) / f"rotated_{degrees}.pdf"
        with open(rotated, "wb") as f:
            writer.write(f)
        return _stream_file(rotated, "application/pdf", filename=rotated.name)


@app.post("/pdf/protect")
async def protect_pdf(file: UploadFile = File(...), password: str = Form(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / file.filename
        with open(input_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        reader = PdfReader(str(input_path))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        protected = Path(tmpdir) / "protected.pdf"
        with open(protected, "wb") as f:
            writer.write(f)
        return _stream_file(protected, "application/pdf", filename=protected.name)


@app.post("/convert/html-to-pdf")
async def html_to_pdf(html: Optional[str] = Form(None), url: Optional[str] = Form(None)):
    logger.info("/convert/html-to-pdf called: url? %s, html? %s", bool(url), bool(html))
    if not html and not url:
        raise HTTPException(400, detail="Provide html or url")
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "page.pdf"
        common_args = ["--enable-local-file-access", "--encoding", "utf-8", "--quiet", "--custom-header", "User-Agent", "Mozilla/5.0 Transformix"]
        if url:
            try:
                subprocess.run(["wkhtmltopdf", *common_args, url, str(output)], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                msg = e.stderr.decode(errors='ignore') or e.stdout.decode(errors='ignore')
                raise HTTPException(400, detail=f"wkhtmltopdf failed: {msg[:500]}")
        else:
            html_path = Path(tmpdir) / "index.html"
            html_path.write_text(html or "", encoding="utf-8")
            try:
                subprocess.run(["wkhtmltopdf", *common_args, str(html_path), str(output)], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                msg = e.stderr.decode(errors='ignore') or e.stdout.decode(errors='ignore')
                raise HTTPException(400, detail=f"wkhtmltopdf failed: {msg[:500]}")
        if not output.exists() or output.stat().st_size == 0:
            raise HTTPException(400, detail="wkhtmltopdf produced empty output")
        logger.info("/convert/html-to-pdf produced %s bytes", output.stat().st_size)
        return _stream_file(output, "application/pdf", filename="page.pdf") 