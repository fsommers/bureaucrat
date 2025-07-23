# Synthetic Document Generator

A comprehensive Python program that generates synthetic business documents using Google Gemini AI for document AI training purposes. Features document analysis, multi-language support, and realistic document generation.

## Features

- **Document Analysis**: Analyze existing document images to extract structure and entities
- **Multi-Language Support**: Generate documents in 40+ languages with culturally appropriate content
- **Google Gemini AI Integration**: Use advanced AI for synthetic entity data generation and document analysis
- **Realistic Document Generation**: HTML documents with embedded CSS optimized for US Letter-size pages
- **Region-Specific Formatting**: Date formats, email domains, and legal text appropriate for each language/region
- **PDF Conversion**: Multiple conversion engines for high-quality PDF output
- **Paper Texture Backgrounds**: Realistic paper backgrounds for authentic printed/scanned document appearance
- **Flexible Workflow**: Traditional manual input or AI-powered document analysis workflow

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
# The system will randomly select different backgrounds for each document
```

## Workflows

### Workflow 1: AI-Powered Document Analysis (Recommended)

Start with an existing document image and generate similar synthetic documents:

#### Step 1: Analyze Document Image
```bash
# Analyze a Thai medical form
python analyze_document.py -i thai_medical_form.jpg -o analysis_output

# Analyze a German invoice
python analyze_document.py -i german_invoice.png -o analysis_output

# Analyze any document image
python analyze_document.py -i document.jpg -o analysis_output --output-file my_analysis.json
```

#### Step 2: Generate Entity Data from Analysis
```bash
# Use analysis results to generate 100 similar documents
python generate_entities.py -a analysis_output/document_analysis.json -c 100

# Override output directory while using analysis
python generate_entities.py -a analysis_output/document_analysis.json -c 50 -o custom_output

# Mix analysis with manual parameters
python generate_entities.py -a my_analysis.json -c 75 -o mixed_mode
```

#### Step 3: Generate HTML Documents
```bash
# Generate HTML documents using the entity data
python generate_documents.py -e output/entity_data.json -o final_documents

# Generate with original document as layout template
python generate_documents.py -e output/entity_data.json -i original_document.jpg -o final_documents
```

#### Step 4: Convert to PDF
```bash
# Convert to PDF with zero margins for edge-to-edge backgrounds
python convert_to_pdf.py -i final_documents
```

### Workflow 2: Traditional Manual Input

Generate documents by specifying parameters manually:

#### Step 1: Generate Entity Data
```bash
# Basic entity generation for catering invoices
python generate_entities.py -t "catering invoice for birthday party" -e "customer name,invoice number,total amount" -c 100

# Thai language entities for medical forms
python generate_entities.py -t "แบบฟอร์มลงทะเบียนผู้ป่วยใหม่" -e "ชื่อผู้ป่วย,เลขบัตรประชาชน,โรงพยาบาล" -c 50 -l th

# German entities for rental agreements
python generate_entities.py -t "Wohnungsmietvertrag" -e "Vermieter Name,Mieter Name,Miete pro Monat" -c 25 -l de

# Spanish entities for consulting agreements
python generate_entities.py -t "contrato de servicios de consultoría" -e "nombre consultor,empresa cliente,tarifa por hora" -c 30 -l es
```

#### Step 2: Generate HTML Documents
```bash
# Generate documents using entity data
python generate_documents.py -e output/entity_data.json

# Generate with custom output directory
python generate_documents.py -e thai_entities/entity_data.json -o thai_documents

# Generate with template image for layout matching
python generate_documents.py -e output/entity_data.json -i template_document.jpg -o templated_docs
```

#### Step 3: Convert to PDF
```bash
# Convert to PDF
python convert_to_pdf.py -i output
```

## Commands Reference

### analyze_document.py
Analyze document images to extract structure and entities.

**Parameters:**
- `-i, --image PATH`: Path to document image file (required) - JPG, PNG, etc.
- `-o, --output TEXT`: Output directory for analysis results (default: analysis_output)
- `--output-file TEXT`: Output JSON filename (default: document_analysis.json)

**Example Output:**
```json
{
  "document_type": "ใบแจ้งหนี้การรักษา",
  "detected_language": "th",
  "confidence": "high",
  "extracted_entities": {
    "ชื่อผู้ป่วย": "สมชาย รักไทย",
    "โรงพยาบาล": "โรงพยาบาลสมิติเวช",
    "ค่ารักษา": "2,500 บาท"
  }
}
```

### generate_entities.py (Enhanced)
Generate synthetic entity data manually or from document analysis.

**Manual Mode Parameters:**
- `-t, --document-type TEXT`: Type of document (required for manual mode)
- `-e, --entity-fields TEXT`: Comma-separated entity fields (required for manual mode)
- `-c, --count INTEGER`: Number of records to generate (required)
- `-l, --language TEXT`: Language code (default: en, 40+ languages supported)

**Analysis Mode Parameters:**
- `-a, --analysis-json PATH`: JSON file from analyze_document.py
- `-c, --count INTEGER`: Number of records to generate (required)

**Common Parameters:**
- `-o, --output-dir TEXT`: Output directory (default: output)
- `-f, --output-file TEXT`: Output JSON filename (default: entity_data.json)

**Supported Languages:** en, th, de, fr, es, ja, ko, zh, ar, hi, pt, ru, it, nl, and 25+ more

### generate_documents.py
Create HTML documents from entity data.

**Parameters:**
- `-e, --entity-file PATH`: JSON file with entity data (required)
- `-t, --document-type TEXT`: Override document type (optional)
- `-l, --language TEXT`: Override language (optional)
- `-i, --template-image PATH`: Image file to use as layout template (optional)
- `-o, --output-dir TEXT`: Output directory (default: output)
- `-s, --start-index INTEGER`: Starting document number (default: 1)

### convert_to_pdf.py
Convert HTML documents to PDF format.

**Parameters:**
- `-i, --html-dir PATH`: Directory with HTML files (required)
- `-o, --output-dir TEXT`: PDF output directory (optional)
- `-c, --converter TEXT`: Conversion engine (weasyprint, wkhtmltopdf, playwright, chrome)
- `-p, --paper-size TEXT`: Paper size (Letter, A4, Legal, default: Letter)
- `--keep-html`: Keep HTML files after conversion
- `--pattern TEXT`: HTML file pattern (default: *.html)

## Regional Features

### Date Formats
- **Thai**: Buddhist Era dates (BE) - "15 มกราคม 2567"
- **German**: DD.MM.YYYY format - "15.01.2024"
- **Japanese**: Era dates - "令和6年1月15日"
- **Chinese**: YYYY年MM月DD日 format - "2024年1月15日"
- **English**: MM/DD/YYYY format - "01/15/2024"

### Email Domains
- **Thai**: @hotmail.co.th, @gmail.com, .co.th domains
- **German**: @web.de, @gmx.de, @t-online.de
- **Japanese**: @yahoo.co.jp, @gmail.com
- **Chinese**: @qq.com, @163.com, @126.com
- **English**: @gmail.com, @yahoo.com, @outlook.com

### Legal Compliance Text
- **Thai**: References Thai Personal Data Protection Act (PDPA)
- **German**: References DSGVO/GDPR, BGB (German Civil Code)
- **English**: References US state laws based on addresses (CCPA, etc.)
- **French**: References RGPD, Code Civil
- **All regions**: Contextually appropriate legal disclaimers

## Example Workflows

### Complete AI-Powered Workflow
```bash
# 1. Analyze an existing Thai medical form
python analyze_document.py -i thai_medical_form.jpg -o analysis

# 2. Generate 50 similar synthetic documents
python generate_entities.py -a analysis/document_analysis.json -c 50 -o thai_medical

# 3. Create HTML documents with Thai content
python generate_documents.py -e thai_medical/entity_data.json -o thai_medical

# 4. Convert to PDF with authentic backgrounds
python convert_to_pdf.py -i thai_medical

# Result: 50 realistic Thai medical forms with proper formatting, 
# Buddhist Era dates, Thai email domains, and PDPA compliance text
```

### Multi-Language Document Generation
```bash
# German rental agreements
python generate_entities.py -t "Wohnungsmietvertrag" -e "Vermieter,Mieter,Adresse,Miete,Kaution" -c 25 -l de
python generate_documents.py -e output/entity_data.json -o german_rentals
python convert_to_pdf.py -i german_rentals

# Japanese employment contracts  
python generate_entities.py -t "雇用契約書" -e "会社名,従業員名,給与,開始日" -c 20 -l ja
python generate_documents.py -e output/entity_data.json -o japanese_contracts
python convert_to_pdf.py -i japanese_contracts
```

### Template-Based Document Generation
```bash
# Generate documents that match existing template layout
python generate_entities.py -t "medical consultation form" -e "patient name,doctor name,diagnosis,treatment" -c 10
python generate_documents.py -e output/entity_data.json -i template_medical_form.jpg -o templated_medical

# Analysis + Template workflow for precise matching
python analyze_document.py -i original_invoice.png -o analysis
python generate_entities.py -a analysis/document_analysis.json -c 25 -o invoice_entities
python generate_documents.py -e invoice_entities/entity_data.json -i original_invoice.png -o matched_invoices
python convert_to_pdf.py -i matched_invoices

# Result: Documents that closely match the original template's layout and appearance
```

## PDF Conversion Engines

### WeasyPrint (Recommended)
```bash
pip install weasyprint
python convert_to_pdf.py -i output -c weasyprint
```
- Pure Python, excellent CSS support, UTF-8 compatible

### wkhtmltopdf
```bash
# Download from https://wkhtmltopdf.org/downloads.html
python convert_to_pdf.py -i output -c wkhtmltopdf
```
- High-quality rendering, webkit-based

### Playwright
```bash
pip install playwright && playwright install chromium
python convert_to_pdf.py -i output -c playwright
```
- Modern browser engine, excellent JavaScript support

### Chrome Headless
```bash
# Install Google Chrome browser
python convert_to_pdf.py -i output -c chrome
```
- Uses actual Chrome browser engine

## Paper Background System

### Enhanced Background Features
- **Per-Document Selection**: Each document gets a unique randomly selected background
- **Zero-Margin PDFs**: Backgrounds extend to page edges without white borders
- **Realistic Textures**: Paper textures, aged paper, document backgrounds

### Setup Instructions
1. **Add PNG Files**: Place background images in `backgrounds/` directory
2. **Recommended Size**: 1200x1600 pixels (US Letter aspect ratio)
3. **Automatic Processing**: System copies and renames backgrounds per document

### File Structure
```
backgrounds/
├── paper_bg_1.png      # Aged paper texture
├── paper_bg_2.png      # Office paper background  
├── paper_bg_3.png      # Vintage document texture
└── paper_bg_4.png      # Subtle watermark pattern
```

## Output Files

1. **Analysis Results**: JSON with document type, language, and extracted entities
2. **Entity Data**: JSON with synthetic entity records and metadata
3. **HTML Documents**: Individual styled documents (document_0001.html, etc.)
4. **Background Images**: Per-document background files (background_0001.png, etc.)
5. **PDF Documents**: Final documents with embedded backgrounds
6. **Document Metadata**: JSON linking documents to entity data

## Advanced Features

### Template-Based Layout Matching
- **Layout Template Images**: Use existing document images as visual templates for HTML generation
- **Precise Layout Replication**: AI analyzes template images and matches positioning, spacing, and structure
- **Visual Design Matching**: Replicates headers, tables, text formatting, and overall document appearance
- **Template Priority**: Template layout takes precedence over generic formatting when `-i` parameter is used

### Font Optimization
- **Reduced Font Sizes**: 11-12px body text, 9-10px legal text for content density
- **UTF-8 Support**: Full international character support
- **Professional Typography**: Optimized header and body text sizing

### Content Enhancement
- **Verbose Text**: 2-3 paragraphs of standard text per document type
- **Legal Disclosures**: Region-specific legal references and compliance text
- **Document-Specific Content**: Medical forms include patient rights, contracts include terms

### Technical Features
- **Zero-Margin PDFs**: Backgrounds extend to page edges
- **Per-Document Backgrounds**: Each document gets unique background selection
- **Language Detection**: Automatic language detection from document analysis
- **Cultural Appropriateness**: Names, addresses, and content appropriate for each region

## Requirements

```
google-generativeai>=0.7.0
jinja2>=3.1.0
click>=8.1.0
python-dotenv>=1.0.0
Pillow>=10.0.0  # Image processing for document analysis

# PDF conversion dependencies (optional)
weasyprint>=60.0  # Recommended
playwright>=1.40.0  # Alternative
```

## License

This project is designed for document AI training and research purposes.