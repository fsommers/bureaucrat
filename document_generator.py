import os
import json
import re
from typing import Dict, List, Any
from jinja2 import Template
from gemini_client import GeminiClient
from config import DEFAULT_OUTPUT_DIR

class DocumentGenerator:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.generated_data = []
    
    
    def generate_documents(self, 
                         document_type: str, 
                         entity_fields: List[str], 
                         count: int, 
                         language: str = 'en',
                         output_dir: str = DEFAULT_OUTPUT_DIR) -> None:
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Step 1: Generating {count} sets of entity data...")
        
        # Step 1: Generate bulk entity data
        entity_data_list = self.gemini_client.generate_bulk_entity_data(
            document_type, entity_fields, count, language
        )
        
        # Save entity data JSON
        entity_json_filepath = os.path.join(output_dir, 'entity_data.json')
        with open(entity_json_filepath, 'w', encoding='utf-8') as f:
            json.dump(entity_data_list, f, indent=2, ensure_ascii=False)
        
        print(f"Entity data saved to: {entity_json_filepath}")
        print(f"Step 2: Generating {count} HTML documents using entity data...")
        
        # Step 2: Generate HTML documents using each entity data record
        for i, entity_data in enumerate(entity_data_list):
            # Generate document with specific entity data
            complete_html = self.gemini_client.generate_document_with_data(
                document_type, entity_data, language
            )
            
            # Save HTML file
            filename = f"document_{i+1:04d}.html"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(complete_html)
            
            # Track generated document
            self.generated_data.append({
                'filename': filename,
                'document_type': document_type,
                'language': language,
                'entity_data': entity_data
            })
            
            print(f"Generated: {filename}")
        
        # Save document metadata JSON
        metadata_json_filepath = os.path.join(output_dir, 'document_metadata.json')
        with open(metadata_json_filepath, 'w', encoding='utf-8') as f:
            json.dump(self.generated_data, f, indent=2, ensure_ascii=False)
        
        print(f"Generated {count} documents in {output_dir}")
        print(f"Entity data saved to: {entity_json_filepath}")
        print(f"Document metadata saved to: {metadata_json_filepath}")
    
    def clear_data(self):
        self.generated_data = []