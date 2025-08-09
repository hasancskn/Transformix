# Transformix

Dosya dönüştürme ve PDF araçları (Docker Compose ile tek komutta çalışır).

## Başlatma

- Gereksinimler: Docker, Docker Compose
- Çalıştırma:

```bash
docker compose up -d --build
```

- Frontend: http://localhost:3000
- Backend (API docs): http://localhost:8000/docs

## Mimarî
- Backend: FastAPI (Python). LibreOffice, Ghostscript, ImageMagick, wkhtmltopdf kullanılır.
- Frontend: React + Vite + Tailwind. Nginx üzerinden servis edilir. `/api` istekleri `backend` servisine yönlendirilir.

## Sağlanan Endpointler
- `POST /convert/word-to-pdf`
- `POST /convert/pdf-to-word`
- `POST /convert/pdf-to-jpg` (ZIP döndürür)
- `POST /convert/jpg-to-pdf`
- `POST /compress/pdf`
- `POST /pdf/merge`
- `POST /pdf/split`
- `POST /pdf/rotate`
- `POST /pdf/protect`
- `POST /convert/html-to-pdf`
- `GET /` tüm yetenekler listesi 