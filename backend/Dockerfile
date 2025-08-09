# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for LibreOffice, Ghostscript, Poppler, ImageMagick etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    ghostscript \
    poppler-utils \
    imagemagick \
    wkhtmltopdf \
    qpdf \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Allow ImageMagick to read/write PDFs (policy tweak)
RUN sed -i 's/<policy domain="coder" rights="none" pattern="PDF"\/>/<policy domain="coder" rights="read|write" pattern="PDF"\/>/' /etc/ImageMagick-6/policy.xml || true

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 