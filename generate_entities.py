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
import json
from ai_providers import get_ai_client
from config import DEFAULT_OUTPUT_DIR, LANGUAGE_CODES, AI_PROVIDER

@click.command()
@click.option('--document-type', '-t', 
              help='Type of document (e.g., "catering invoice for birthday party", "medical consultation report")')
@click.option('--entity-fields', '-e', 
              help='Comma-separated list of entity fields (e.g., "customer name,invoice number,total amount")')
@click.option('--count', '-c', type=int,
              help='Number of entity records to generate')
@click.option('--language', '-l', default='en',
              help=f'Language code for entity generation (default: en). Supported: {", ".join(sorted(LANGUAGE_CODES.keys()))}')
@click.option('--analysis-json', '-a', type=click.Path(exists=True),
              help='JSON file from analyze_document.py containing document_type, detected_language, and extracted_entities')
@click.option('--output-dir', '-o', default=DEFAULT_OUTPUT_DIR,
              help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})')
@click.option('--output-file', '-f', default='entity_data.json',
              help='Output JSON filename (default: entity_data.json)')
def generate_entities(document_type, entity_fields, count, language, analysis_json, output_dir, output_file):
    """
    Generate synthetic entity data using AI providers.

    This command generates bulk entity data that can later be used to create HTML documents.
    
    You can provide parameters manually OR use JSON output from analyze_document.py:
    
    Manual mode:
    python generate_entities.py -t "catering invoice" -e "customer name,amount" -c 100
    
    JSON analysis mode:
    python generate_entities.py -a document_analysis.json -c 50
    
    Mixed mode (JSON + manual count):
    python generate_entities.py -a analysis.json -c 100 -o custom_output
    """
    
    # Handle JSON input mode
    if analysis_json:
        try:
            with open(analysis_json, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            # Extract data from JSON
            json_document_type = analysis_data.get('document_type', '')
            json_language = analysis_data.get('detected_language', 'en')
            json_entities = analysis_data.get('extracted_entities', {})
            
            # Use JSON values if manual parameters not provided
            if not document_type:
                document_type = json_document_type
            if not entity_fields:
                # Extract entity field names from the analysis
                entity_fields = ','.join(json_entities.keys()) if json_entities else ''
            if language == 'en' and json_language:
                # Only override default language if not explicitly set
                language = json_language
                
            click.echo(f"📄 Loaded analysis from: {analysis_json}")
            click.echo(f"🔍 JSON Document Type: {json_document_type}")
            click.echo(f"🌐 JSON Language: {json_language}")
            click.echo(f"📊 JSON Entities: {list(json_entities.keys())}")
            click.echo()
            
        except Exception as e:
            click.echo(f"❌ Error reading analysis JSON: {e}")
            return 1
    
    # Validate required parameters
    if not document_type:
        click.echo("Error: Document type must be specified (use -t or provide -a with valid JSON)")
        return 1
    
    if not entity_fields:
        click.echo("Error: Entity fields must be specified (use -e or provide -a with extracted entities)")
        return 1
        
    if not count:
        click.echo("Error: Count must be specified (use -c)")
        return 1
    
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
        
        # Use the AI provider system for flexibility
        client = get_ai_client(provider=AI_PROVIDER)
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