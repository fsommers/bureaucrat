#!/usr/bin/env python3

# Copyright 2025 Frank Sommers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click
import os
import glob
import re
from pathlib import Path

@click.command()
@click.option('--html-dir', '-i', required=True,
              help='Directory containing HTML files to convert')
@click.option('--output-dir', '-o', default=None,
              help='Output directory for PDF files (default: same as HTML directory)')
@click.option('--converter', '-c', default='weasyprint', 
              type=click.Choice(['weasyprint', 'wkhtmltopdf', 'playwright', 'chrome']),
              help='PDF conversion tool to use (default: weasyprint)')
@click.option('--paper-size', '-p', default='Letter',
              type=click.Choice(['Letter', 'A4', 'Legal']),
              help='Paper size for PDF (default: Letter)')
@click.option('--pattern', default='*.html',
              help='File pattern to match HTML files (default: *.html)')
@click.option('--keep-html', is_flag=True,
              help='Keep HTML files after conversion (default: delete them)')
def convert_to_pdf(html_dir, output_dir, converter, paper_size, pattern, keep_html):
    """
    Convert HTML files to PDF documents.
    
    This command converts all HTML files in a directory to PDF format using
    various conversion tools.
    
    Examples:
    
    python convert_to_pdf.py -i output
    
    python convert_to_pdf.py -i output -o pdfs -c wkhtmltopdf
    
    python convert_to_pdf.py -i contracts -o contract_pdfs --keep-html
    """
    
    # Validate input directory
    if not os.path.exists(html_dir):
        click.echo(f"Error: HTML directory not found: {html_dir}")
        return 1
    
    # Set output directory
    if output_dir is None:
        output_dir = html_dir
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find HTML files
    html_pattern = os.path.join(html_dir, pattern)
    html_files = glob.glob(html_pattern)
    
    if not html_files:
        click.echo(f"No HTML files found matching pattern: {pattern} in {html_dir}")
        return 1
    
    # Sort files for consistent processing
    html_files.sort()
    
    # Display configuration
    click.echo(f"HTML Directory: {html_dir}")
    click.echo(f"Output Directory: {output_dir}")
    click.echo(f"Converter: {converter}")
    click.echo(f"Paper Size: {paper_size}")
    click.echo(f"HTML Files Found: {len(html_files)}")
    click.echo(f"Keep HTML: {keep_html}")
    click.echo()
    
    try:
        # Convert files based on selected converter
        if converter == 'weasyprint':
            success = convert_with_weasyprint(html_files, output_dir, paper_size)
        elif converter == 'wkhtmltopdf':
            success = convert_with_wkhtmltopdf(html_files, output_dir, paper_size)
        elif converter == 'playwright':
            success = convert_with_playwright(html_files, output_dir, paper_size)
        elif converter == 'chrome':
            success = convert_with_chrome(html_files, output_dir, paper_size)
        
        if not success:
            return 1
        
        # Delete HTML files if requested
        if not keep_html:
            click.echo("\nRemoving HTML files...")
            for html_file in html_files:
                os.remove(html_file)
                click.echo(f"Deleted: {os.path.basename(html_file)}")
        
        click.echo(f"✅ Successfully converted {len(html_files)} HTML files to PDF!")
        click.echo(f"📁 PDF files saved to: {os.path.abspath(output_dir)}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        return 1

def shorten_filename(filename, max_length=16):
    """
    Shorten filename to max_length while preserving ending numbers.
    
    Args:
        filename: Original filename (without extension)
        max_length: Maximum length for the result (default: 16)
    
    Returns:
        Shortened filename preserving ending numbers
    """
    if len(filename) <= max_length:
        return filename
    
    # Check if filename ends with numbers (e.g., _0001, _123, etc.)
    match = re.search(r'(_\d+)$', filename)
    
    if match:
        # Extract the ending number part
        ending_number = match.group(1)
        # Get the base name without the ending number
        base_name = filename[:-len(ending_number)]
        # Calculate how much space we have for the base name
        available_length = max_length - len(ending_number)
        
        if available_length > 0:
            # Shorten the base name and add the ending number
            shortened_base = base_name[:available_length]
            return shortened_base + ending_number
        else:
            # If ending number is too long, just truncate the whole thing
            return filename[:max_length]
    else:
        # No ending number, just truncate
        return filename[:max_length]

def unique_pdf_path(output_dir, shortened_name):
    """Return a PDF path in output_dir that won't overwrite an existing file."""
    pdf_path = os.path.join(output_dir, f"{shortened_name}.pdf")
    if not os.path.exists(pdf_path):
        return pdf_path
    counter = 2
    while True:
        candidate = os.path.join(output_dir, f"{shortened_name}_v{counter}.pdf")
        if not os.path.exists(candidate):
            return candidate
        counter += 1

def convert_with_weasyprint(html_files, output_dir, paper_size):
    """Convert HTML files to PDF using WeasyPrint"""
    try:
        import weasyprint
    except ImportError:
        click.echo("❌ WeasyPrint not installed. Install with: pip install weasyprint")
        return False
    
    click.echo("Converting with WeasyPrint...")
    
    for html_file in html_files:
        try:
            # Generate PDF filename
            html_name = Path(html_file).stem
            shortened_name = shorten_filename(html_name)
            pdf_path = unique_pdf_path(output_dir, shortened_name)

            # Convert to PDF with proper encoding and font support
            html_doc = weasyprint.HTML(filename=html_file, encoding='utf-8')
            
            # Enhanced CSS with font support for international characters and zero margins
            css_content = f"""
            @page {{ 
                size: {paper_size}; 
                margin: 0; 
            }}
            @font-face {{
                font-family: 'DejaVu Sans';
                src: url('data:font/truetype;base64,') format('truetype');
            }}
            * {{
                font-family: 'DejaVu Sans', 'Arial Unicode MS', Arial, sans-serif !important;
            }}
            """
            
            css = weasyprint.CSS(string=css_content)
            html_doc.write_pdf(pdf_path, stylesheets=[css], 
                             presentational_hints=True, 
                             optimize_images=True)
            
            click.echo(f"Converted: {os.path.basename(html_file)} → {os.path.basename(pdf_path)}")
            
        except Exception as e:
            click.echo(f"❌ Failed to convert {os.path.basename(html_file)}: {e}")
            return False
    
    return True

def convert_with_wkhtmltopdf(html_files, output_dir, paper_size):
    """Convert HTML files to PDF using wkhtmltopdf"""
    import subprocess
    import shutil
    
    # Check if wkhtmltopdf is installed
    if not shutil.which('wkhtmltopdf'):
        click.echo("❌ wkhtmltopdf not installed. Install from: https://wkhtmltopdf.org/downloads.html")
        return False
    
    click.echo("Converting with wkhtmltopdf...")
    
    # Set paper size format
    paper_formats = {
        'Letter': 'Letter',
        'A4': 'A4',
        'Legal': 'Legal'
    }
    
    for html_file in html_files:
        try:
            # Generate PDF filename
            html_name = Path(html_file).stem
            shortened_name = shorten_filename(html_name)
            pdf_path = unique_pdf_path(output_dir, shortened_name)

            # Build command with UTF-8 encoding support and zero margins
            cmd = [
                'wkhtmltopdf',
                '--page-size', paper_formats[paper_size],
                '--margin-top', '0',
                '--margin-bottom', '0',
                '--margin-left', '0',
                '--margin-right', '0',
                '--print-media-type',
                '--encoding', 'UTF-8',
                '--disable-smart-shrinking',
                '--enable-local-file-access',
                html_file,
                pdf_path
            ]
            
            # Execute conversion
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                click.echo(f"Converted: {os.path.basename(html_file)} → {os.path.basename(pdf_path)}")
            else:
                click.echo(f"❌ Failed to convert {os.path.basename(html_file)}: {result.stderr}")
                return False
                
        except Exception as e:
            click.echo(f"❌ Failed to convert {os.path.basename(html_file)}: {e}")
            return False
    
    return True

def convert_with_playwright(html_files, output_dir, paper_size):
    """Convert HTML files to PDF using Playwright"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        click.echo("❌ Playwright not installed. Install with: pip install playwright && playwright install chromium")
        return False
    
    click.echo("Converting with Playwright...")
    
    # Set paper format
    paper_formats = {
        'Letter': {'width': '8.5in', 'height': '11in'},
        'A4': {'width': '8.27in', 'height': '11.7in'},
        'Legal': {'width': '8.5in', 'height': '14in'}
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        for html_file in html_files:
            try:
                # Generate PDF filename
                html_name = Path(html_file).stem
                shortened_name = shorten_filename(html_name)
                pdf_path = unique_pdf_path(output_dir, shortened_name)

                # Load HTML file with proper encoding
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Set content with proper encoding
                page.set_content(html_content)
                
                # Wait for content to load
                page.wait_for_load_state('networkidle')
                
                # Convert to PDF with enhanced options and zero margins
                page.pdf(
                    path=pdf_path,
                    format=paper_size,
                    margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'},
                    print_background=True,
                    prefer_css_page_size=True,
                    display_header_footer=False
                )
                
                click.echo(f"Converted: {os.path.basename(html_file)} → {os.path.basename(pdf_path)}")
                
            except Exception as e:
                click.echo(f"❌ Failed to convert {os.path.basename(html_file)}: {e}")
                browser.close()
                return False
        
        browser.close()
    
    return True

def convert_with_chrome(html_files, output_dir, paper_size):
    """Convert HTML files to PDF using Chrome/Chromium headless"""
    import subprocess
    import shutil
    
    # Find Chrome/Chromium executable
    chrome_paths = [
        'google-chrome',
        'chromium-browser',
        'chromium',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
    ]
    
    chrome_exe = None
    for path in chrome_paths:
        if shutil.which(path) or os.path.exists(path):
            chrome_exe = path
            break
    
    if not chrome_exe:
        click.echo("❌ Chrome/Chromium not found. Please install Google Chrome or Chromium.")
        return False
    
    click.echo("Converting with Chrome headless...")
    
    for html_file in html_files:
        try:
            # Generate PDF filename
            html_name = Path(html_file).stem
            shortened_name = shorten_filename(html_name)
            pdf_path = unique_pdf_path(output_dir, shortened_name)

            # Build command
            cmd = [
                chrome_exe,
                '--headless',
                '--disable-gpu',
                '--print-to-pdf=' + pdf_path,
                f'--print-to-pdf-no-header',
                f'--virtual-time-budget=5000',
                f'file://{os.path.abspath(html_file)}'
            ]
            
            # Execute conversion
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(pdf_path):
                click.echo(f"Converted: {os.path.basename(html_file)} → {os.path.basename(pdf_path)}")
            else:
                click.echo(f"❌ Failed to convert {os.path.basename(html_file)}")
                return False
                
        except Exception as e:
            click.echo(f"❌ Failed to convert {os.path.basename(html_file)}: {e}")
            return False
    
    return True

if __name__ == '__main__':
    convert_to_pdf()