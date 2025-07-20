#!/usr/bin/env python3

from gemini_client import GeminiClient

def test_entity_generation():
    print("Testing entity generation...")
    
    try:
        client = GeminiClient()
        
        # Test with a simple example
        document_type = "catering invoice for birthday party"
        entity_fields = ["company name", "customer name", "total amount"]
        count = 2
        language = "en"
        
        print(f"Generating {count} entities for: {document_type}")
        print(f"Entity fields: {entity_fields}")
        print()
        
        result = client.generate_bulk_entity_data(document_type, entity_fields, count, language)
        
        print("Result:")
        print(result)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_entity_generation()