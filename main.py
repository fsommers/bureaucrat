#!/usr/bin/env python3

import click
import os
from document_generator import DocumentGenerator
from config import DEFAULT_OUTPUT_DIR, DEFAULT_DOCUMENT_COUNT, LANGUAGE_CODES

@click.command()
@click.option('--document-type', '-t', required=True, 
              help='Type of document to generate (e.g., "business invoice for catering party")')
@click.option('--entity-fields', '-e', required=True,
              help='Comma-separated list of entity fields (e.g., "customer name,employee name,date")')
@click.option('--count', '-c', default=DEFAULT_DOCUMENT_COUNT, type=int,
              help=f'Number of documents to generate (default: {DEFAULT_DOCUMENT_COUNT})')
@click.option('--language', '-l', default='en',
              help=f'Language code for document generation (default: en). Supported: {", ".join(sorted(LANGUAGE_CODES.keys()))}')
@click.option('--output-dir', '-o', default=DEFAULT_OUTPUT_DIR,
              help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})')
def generate(document_type, entity_fields, count, language, output_dir):
    """
    Generate synthetic business documents using Google Gemini AI.
    
    Examples:
    
    python main.py -t "business invoice for catering party" -e "customer name,invoice number,date,total amount" -c 50
    
    python main.py -t "non-disclosure agreement for software consulting" -e "company name,consultant name,project description,start date" -c 10 -l th
    """
    
    # Parse entity fields
    fields = [field.strip() for field in entity_fields.split(',')]
    
    # Validate inputs
    if count <= 0:
        click.echo("Error: Count must be greater than 0")
        return
    
    if not fields:
        click.echo("Error: At least one entity field must be specified")
        return
    
    # Validate language code
    if language not in LANGUAGE_CODES:
        click.echo(f"Error: Unsupported language code '{language}'")
        click.echo(f"Supported language codes: {', '.join(sorted(LANGUAGE_CODES.keys()))}")
        return
    
    # Display configuration
    click.echo(f"Document Type: {document_type}")
    click.echo(f"Entity Fields: {', '.join(fields)}")
    click.echo(f"Count: {count}")
    click.echo(f"Language: {language}")
    click.echo(f"Output Directory: {output_dir}")
    click.echo()
    
    try:
        # Generate documents
        generator = DocumentGenerator()
        generator.generate_documents(
            document_type=document_type,
            entity_fields=fields,
            count=count,
            language=language,
            output_dir=output_dir
        )
        
        click.echo(f"\n✅ Successfully generated {count} documents!")
        click.echo(f"📁 Files saved to: {os.path.abspath(output_dir)}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        return 1

if __name__ == '__main__':
    generate()