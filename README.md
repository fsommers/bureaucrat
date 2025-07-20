# Synthetic Document Generator

A Python program that generates synthetic business documents using Google Gemini AI for document AI training purposes.

## Features

- Generate business-like documents in multiple languages (English and Thai)
- Use Google Gemini API for synthetic entity data generation
- Generate HTML documents with embedded CSS optimized for US Letter-size pages
- Three-step process: entity data generation + document creation + PDF conversion
- Visually rich, print-ready documents with professional styling
- Realistic paper texture backgrounds for authentic printed/scanned document appearance
- Command-line interface for easy usage

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Google Gemini API key:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

3. Add background images (optional):
```bash
# Place PNG files in the backgrounds/ directory for realistic paper textures
# The system will randomly select one background for each document generation batch
```

## Usage

The document generation process has three main steps:

### Step 1: Generate Entity Data

Generate synthetic entity data first:

```bash
# Basic entity generation for catering invoices
python generate_entities.py -t "catering invoice for birthday party" -e "customer name,invoice number,total amount" -c 100

# Thai language entities for employment contracts
python generate_entities.py -t "employment contract" -e "company name,employee name,salary" -c 50 -l th -o thai_entities

# Spanish entities for automotive invoices
python generate_entities.py -t "automotive repair invoice" -e "shop name,customer name,service description,cost" -c 30 -l es

# Japanese entities for medical reports
python generate_entities.py -t "medical consultation report" -e "clinic name,patient name,diagnosis,fee" -c 25 -l ja -f medical_entities.json

# French entities for consulting agreements
python generate_entities.py -t "consulting service agreement" -e "consultant name,client company,project scope,hourly rate" -c 15 -l fr
```

### Step 2: Generate HTML Documents

Use the entity data to create HTML documents:

```bash
# Basic document generation (uses document type from entity file)
python generate_documents.py -e output/entity_data.json

# Thai language documents (uses settings from entity file)
python generate_documents.py -e thai_entities/entity_data.json -o contracts

# Override document type and custom starting index
python generate_documents.py -e medical_entities.json -t "custom medical report" -s 100
```

### Step 3: Convert HTML to PDF

Convert the generated HTML files to PDF format:

```bash
# Basic PDF conversion using WeasyPrint (recommended)
python convert_to_pdf.py -i output

# Convert with different tool and keep HTML files
python convert_to_pdf.py -i output -o pdfs -c wkhtmltopdf --keep-html

# Convert Thai contracts to A4 format
python convert_to_pdf.py -i contracts -o contract_pdfs -p A4

# Convert using Playwright browser engine
python convert_to_pdf.py -i output -c playwright
```

### Legacy Single-Step Command

The original combined approach is still available:

```bash
python main.py -t "business invoice for catering party" -e "customer name,invoice number,date,total amount" -c 10
```

## Command Parameters

### generate_entities.py
- `-t, --document-type`: Type of document (required, e.g., "catering invoice for birthday party")
- `-e, --entity-fields`: Comma-separated list of entity fields (required)
- `-c, --count`: Number of entity records to generate (required)
- `-l, --language`: Language code (default: en). Supports 40+ languages including en, th, es, fr, de, ja, ko, zh, ar, hi, etc.
- `-o, --output-dir`: Output directory (default: output)
- `-f, --output-file`: Output JSON filename (default: entity_data.json)

### generate_documents.py
- `-e, --entity-file`: Path to JSON file containing entity data (required)
- `-t, --document-type`: Override document type (optional, uses type from entity file)
- `-l, --language`: Override language code (optional, uses language from entity file)
- `-o, --output-dir`: Output directory for HTML documents (default: output)
- `-s, --start-index`: Starting index for document numbering (default: 1)

### convert_to_pdf.py
- `-i, --html-dir`: Directory containing HTML files to convert (required)
- `-o, --output-dir`: Output directory for PDF files (optional, defaults to HTML directory)
- `-c, --converter`: PDF conversion tool (weasyprint, wkhtmltopdf, playwright, chrome, default: weasyprint)
- `-p, --paper-size`: Paper size for PDF (Letter, A4, Legal, default: Letter)
- `--pattern`: File pattern to match HTML files (default: *.html)
- `--keep-html`: Keep HTML files after conversion (default: delete them)

## Output Files

1. **Entity Data**: JSON file with synthetic entity records
2. **HTML Documents**: Individual HTML files (document_0001.html, document_0002.html, etc.)  
3. **PDF Documents**: Individual PDF files (document_0001.pdf, document_0002.pdf, etc.)
4. **Document Metadata**: JSON file linking each document to its entity data

## Example Workflow

```bash
# 1. Generate 100 entity records for catering invoices
python generate_entities.py -t "catering invoice for birthday party" -e "customer name,invoice number,date,total amount,line items" -c 100

# 2. Create 100 invoice documents using the entity data (document type is read from entity file)
python generate_documents.py -e output/entity_data.json

# 3. Convert HTML documents to PDF format
python convert_to_pdf.py -i output

# 4. Generated files:
# - output/entity_data.json (100 entity records with _document_type and _language fields)
# - output/document_0001.pdf through document_0100.pdf (HTML files are deleted after conversion)
# - output/document_metadata.json (links documents to entity data)
```

## PDF Conversion Methods

The `convert_to_pdf.py` command supports multiple PDF conversion engines:

### WeasyPrint (Recommended)
- **Installation**: `pip install weasyprint`
- **Pros**: Pure Python, excellent CSS support, easy to install
- **Usage**: `python convert_to_pdf.py -i output -c weasyprint`

### wkhtmltopdf
- **Installation**: Download from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html)
- **Pros**: High-quality rendering, webkit-based
- **Usage**: `python convert_to_pdf.py -i output -c wkhtmltopdf`

### Playwright
- **Installation**: `pip install playwright && playwright install chromium`
- **Pros**: Modern browser engine, excellent JavaScript support
- **Usage**: `python convert_to_pdf.py -i output -c playwright`

### Chrome Headless
- **Installation**: Install Google Chrome or Chromium browser
- **Pros**: Uses actual Chrome browser engine
- **Usage**: `python convert_to_pdf.py -i output -c chrome`

## Installation Guide

```bash
# Install Python dependencies
pip install -r requirements.txt

# For WeasyPrint (recommended)
pip install weasyprint

# For Playwright
pip install playwright
playwright install chromium

# For wkhtmltopdf - download and install from website
# For Chrome - install Google Chrome browser
```

## Paper Background Textures

To make your generated PDFs look like real printed/scanned documents:

1. **Add Background Images**: Place PNG files in the `backgrounds/` directory
2. **Image Requirements**:
   - Format: PNG files only
   - Recommended size: 1200x1600 pixels (US Letter aspect ratio)
   - Content: Paper textures, aged paper, document backgrounds
3. **Automatic Selection**: The system randomly selects one background per document generation batch
4. **Result**: All documents in a batch will have the same realistic paper texture background

### Example Background Types:
- Scanned paper textures
- Aged/vintage paper backgrounds
- Subtle watermark patterns  
- Document texture overlays

### File Structure:
```
backgrounds/
├── aged_paper_01.png
├── parchment_texture.png
├── office_paper.png
└── vintage_document.png
```