#!/usr/bin/env python3

import click
import os
import json
from gemini_client import GeminiClient
from config import DEFAULT_OUTPUT_DIR, LANGUAGE_CODES

@click.command()
@click.option('--document-type', '-t', required=True,
              help='Type of document (e.g., "catering invoice for birthday party", "medical consultation report")')
@click.option('--entity-fields', '-e', required=True,
              help='Comma-separated list of entity fields (e.g., "customer name,invoice number,total amount")')
@click.option('--count', '-c', required=True, type=int,
              help='Number of entity records to generate')
@click.option('--language', '-l', default='en',
              help=f'Language code for entity generation (default: en). Supported: {", ".join(sorted(LANGUAGE_CODES.keys()))}')
@click.option('--output-dir', '-o', default=DEFAULT_OUTPUT_DIR,
              help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})')
@click.option('--output-file', '-f', default='entity_data.json',
              help='Output JSON filename (default: entity_data.json)')
def generate_entities(document_type, entity_fields, count, language, output_dir, output_file):
    """
    Generate synthetic entity data using Google Gemini AI.
    
    This command generates bulk entity data that can later be used to create HTML documents.
    
    Examples:
    
    python generate_entities.py -t "catering invoice for birthday party" -e "customer name,invoice number,total amount" -c 100
    
    python generate_entities.py -t "employment contract" -e "company name,employee name,salary" -c 50 -l th -o thai_entities
    """
    
    # Parse entity fields
    fields = [field.strip() for field in entity_fields.split(',')]
    
    # Validate inputs
    if count <= 0:
        click.echo("Error: Count must be greater than 0")
        return 1
    
    if not fields:
        click.echo("Error: At least one entity field must be specified")
        return 1
    
    # Validate language code
    if language not in LANGUAGE_CODES:
        click.echo(f"Error: Unsupported language code '{language}'")
        click.echo(f"Supported language codes: {', '.join(sorted(LANGUAGE_CODES.keys()))}")
        return 1
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Display configuration
    click.echo(f"Document Type: {document_type}")
    click.echo(f"Entity Fields: {', '.join(fields)}")
    click.echo(f"Count: {count}")
    click.echo(f"Language: {language}")
    click.echo(f"Output Directory: {output_dir}")
    click.echo(f"Output File: {output_file}")
    click.echo()
    
    try:
        # Generate entity data
        click.echo(f"Generating {count} sets of entity data...")
        
        client = GeminiClient()
        entity_data_list = client.generate_bulk_entity_data(document_type, fields, count, language)
        
        # Save entity data JSON
        output_path = os.path.join(output_dir, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(entity_data_list, f, indent=2, ensure_ascii=False)
        
        click.echo(f"✅ Successfully generated {len(entity_data_list)} entity records!")
        click.echo(f"📁 Entity data saved to: {os.path.abspath(output_path)}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        return 1

if __name__ == '__main__':
    generate_entities()