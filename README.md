# Transformix

Dosya dönüştürme ve PDF araçları. Tamamen Docker Compose ile çalışır; lokal kurulum gerekmez.

## Hızlı Başlangıç

- Gereksinimler: Docker, Docker Compose
- Çalıştırma:

```bash
docker compose up -d --build
```

- Frontend: http://localhost:3000
- Backend (OpenAPI): http://localhost:8000/docs

## Mimari
- Backend: FastAPI (Python)
  - Araçlar: LibreOffice, Ghostscript, Poppler (pdftoppm), ImageMagick, wkhtmltopdf, qpdf
- Frontend: React + Vite + Tailwind (Nginx ile servis edilir)
  - Karanlık/Aydınlık tema, modern kart arayüzü
  - Tüm özellikler backend kök `/` uç noktasındaki capability listesinden otomatik oluşur


## Desteklenen Özellikler ve Endpointler

Dönüştürme
- `POST /convert/word-to-pdf`
- `POST /convert/pdf-to-word`
- `POST /convert/ppt-to-pdf`
- `POST /convert/excel-to-pdf`
- `POST /convert/pdf-to-jpg` (ZIP döner)
- `POST /convert/jpg-to-pdf`
- `POST /convert/html-to-pdf` (param: `url` veya `html`)
- `POST /convert/images-to-pdf` (çoklu resim)
- `POST /convert/pdf-to-pptx` (her sayfa → bir slayt görseli)
- `POST /convert/pdf-to-excel` (metin satırlarını sayfalara göre aktarır)

PDF Araçları
- `POST /compress/pdf` (param: `quality`)
- `POST /pdf/merge` (çoklu dosya)
- `POST /pdf/split` (param: `from_page`, `to_page`)
- `POST /pdf/rotate` (param: `degrees`)
- `POST /pdf/protect` (param: `password`)
- `POST /pdf/unlock` (param: `password`)
- `POST /pdf/watermark` (param: `text` opsiyonel, `image` opsiyonel, `opacity`, `size`)
- `POST /pdf/page-numbers` (param: `start`, `format`, `position`, `size`)
- `POST /pdf/delete-pages` (param: `pages` → ör. `1,3,5-7`)
- `POST /pdf/reorder` (param: `order` → ör. `3,1,2`)

Kök liste
- `GET /` → Tüm desteklenen dönüşümleri JSON olarak döner; frontend bu listeyi kullanır

## Hızlı Kullanım Örnekleri (curl)

Word → PDF
```bash
curl -s -X POST http://localhost:8000/convert/word-to-pdf \
  -F file=@doc.docx -o out.pdf
```

PDF → Word
```bash
curl -s -X POST http://localhost:8000/convert/pdf-to-word \
  -F file=@in.pdf -o out.docx
```

PDF → JPG (her sayfa için JPG, ZIP olarak döner)
```bash
curl -s -X POST http://localhost:8000/convert/pdf-to-jpg \
  -F file=@in.pdf -o pages.zip
```

JPG → PDF
```bash
curl -s -X POST http://localhost:8000/convert/jpg-to-pdf \
  -F file=@img.jpg -o out.pdf
```

HTML → PDF (URL ile)
```bash
curl -s -X POST http://localhost:8000/convert/html-to-pdf \
  -F url=https://example.com -o page.pdf
```

HTML → PDF (ham HTML ile)
```bash
curl -s -X POST http://localhost:8000/convert/html-to-pdf \
  -F html='<h1>Merhaba</h1>' -o page.pdf
```

Images → PDF (çoklu görsel)
```bash
curl -s -X POST http://localhost:8000/convert/images-to-pdf \
  -F files=@1.jpg -F files=@2.png -o images.pdf
```

PDF → PowerPoint (PPTX)
```bash
curl -s -X POST http://localhost:8000/convert/pdf-to-pptx \
  -F file=@in.pdf -o slides.pptx
```

PDF → Excel (XLSX)
```bash
curl -s -X POST http://localhost:8000/convert/pdf-to-excel \
  -F file=@in.pdf -o extract.xlsx
```

Sıkıştır (Compress)
```bash
curl -s -X POST http://localhost:8000/compress/pdf \
  -F file=@in.pdf -F quality=85 -o compressed.pdf
```

Birleştir (Merge)
```bash
curl -s -X POST http://localhost:8000/pdf/merge \
  -F files=@a.pdf -F files=@b.pdf -o merged.pdf
```

Böl (Split)
```bash
curl -s -X POST http://localhost:8000/pdf/split \
  -F file=@in.pdf -F from_page=3 -F to_page=7 -o part.pdf
```

Döndür (Rotate)
```bash
curl -s -X POST http://localhost:8000/pdf/rotate \
  -F file=@in.pdf -F degrees=90 -o rotated.pdf
```

Koru (Protect)
```bash
curl -s -X POST http://localhost:8000/pdf/protect \
  -F file=@in.pdf -F password=1234 -o protected.pdf
```

Kilidi Kaldır (Unlock)
```bash
curl -s -X POST http://localhost:8000/pdf/unlock \
  -F file=@protected.pdf -F password=1234 -o unlocked.pdf
```

Filigran (Watermark)
```bash
curl -s -X POST http://localhost:8000/pdf/watermark \
  -F file=@in.pdf -F text="Gizli" -F opacity=0.2 -F size=48 -o wm.pdf
```

Sayfa Numaraları (Page Numbers)
```bash
curl -s -X POST http://localhost:8000/pdf/page-numbers \
  -F file=@in.pdf -F start=1 -F format="{n}" -F position=bottom-right -F size=10 -o numbered.pdf
```

Sayfa Silme
```bash
curl -s -X POST http://localhost:8000/pdf/delete-pages \
  -F file=@in.pdf -F pages="1,3,5-7" -o pruned.pdf
```

Sayfa Sıralama
```bash
curl -s -X POST http://localhost:8000/pdf/reorder \
  -F file=@in.pdf -F order="3,1,2" -o reordered.pdf
```

## Notlar
- Büyük dosyalar için Nginx `client_max_body_size 200m` ve uzun istekler için uygun timeout ayarları yapılmıştır.
- Bazı dış siteler `wkhtmltopdf` ile görüntülenmeyebilir; HTML metni vererek dönüştürme yapabilirsiniz.

## Geliştirme
- Değişiklikten sonra yeniden derleme:

```bash
docker compose build backend && docker compose restart backend
# veya
docker compose build frontend && docker compose restart frontend
```

## Lisans
MIT 