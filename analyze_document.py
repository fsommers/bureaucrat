#!/usr/bin/env python3

import click
import json
import os
from pathlib import Path
from ai_providers import get_ai_client
from config import AI_PROVIDER

@click.command()
@click.option('-i', '--image', 'image_file', required=True, type=click.Path(exists=True), 
              help='Path to the document image file')
@click.option('-o', '--output', 'output_dir', default='analysis_output', 
              help='Output directory for analysis results (default: analysis_output)')
@click.option('--output-file', 'output_file', default='document_analysis.json',
              help='Output JSON filename (default: document_analysis.json)')
def analyze_document(image_file, output_dir, output_file):
    """
    Analyze a document image to extract document type and personally identifying information.

    Uses AI vision capabilities to identify document type and extract entities like:
    - Personal names, addresses, phone numbers
    - Company names, addresses, websites, emails
    - Document-specific information
    
    Results are returned in the document's detected language.
    """
    
    click.echo(f"Document Image: {image_file}")
    click.echo(f"Output Directory: {output_dir}")
    click.echo(f"Output File: {output_file}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize AI client using the provider system
    client = get_ai_client(provider=AI_PROVIDER)
    
    try:
        # Analyze the document image
        click.echo("\n🔍 Analyzing document image...")
        analysis_result = client.analyze_document_image(image_file)
        
        # Save results to JSON file
        output_path = os.path.join(output_dir, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        # Display summary
        document_type = analysis_result.get('document_type', 'Unknown')
        language = analysis_result.get('detected_language', 'Unknown')
        entities = analysis_result.get('extracted_entities', {})
        
        click.echo(f"\n✅ Document analysis completed!")
        click.echo(f"📄 Document Type: {document_type}")
        click.echo(f"🌐 Detected Language: {language}")
        click.echo(f"📊 Extracted {len(entities)} entities")
        click.echo(f"💾 Analysis saved to: {output_path}")
        
        # Display extracted entities summary
        if entities:
            click.echo(f"\n📋 Extracted Entities:")
            for entity_name, entity_value in entities.items():
                # Truncate long values for display
                display_value = str(entity_value)
                if len(display_value) > 50:
                    display_value = display_value[:47] + "..."
                click.echo(f"  • {entity_name}: {display_value}")
        
    except Exception as e:
        click.echo(f"❌ Error analyzing document: {e}")
        return 1

if __name__ == '__main__':
    analyze_document()