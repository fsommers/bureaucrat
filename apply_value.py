#!/usr/bin/env python3
"""
Apply values from one entities file to another by replacing attribute values.

This command takes two JSON entities files and replaces values from one attribute 
in the target file with values from another attribute in the source file.

Usage:
    python apply_value.py <from_entities_file> <to_entities_file> <from_attribute> <to_attribute>

Example:
    python apply_value.py from.json to.json full_name "Customer Name"
"""

import json
import sys
import argparse
from typing import List, Dict, Any


def load_entities_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load and validate a JSON entities file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of entity dictionaries
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If file doesn't contain a list of objects
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            raise ValueError(f"File {file_path} must contain a JSON array, got {type(data).__name__}")
            
        if not all(isinstance(item, dict) for item in data):
            raise ValueError(f"All items in {file_path} must be JSON objects")
            
        return data
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Entities file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e}")


def save_entities_file(file_path: str, entities: List[Dict[str, Any]]) -> None:
    """
    Save entities list back to JSON file.
    
    Args:
        file_path: Path to save the file
        entities: List of entity dictionaries to save
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)


def apply_values(from_entities: List[Dict[str, Any]], 
                to_entities: List[Dict[str, Any]],
                from_attribute: str, 
                to_attribute: str) -> List[Dict[str, Any]]:
    """
    Apply values from one entities list to another by replacing attribute values.
    
    Args:
        from_entities: Source entities list
        to_entities: Target entities list (will be modified)
        from_attribute: Attribute name in source entities
        to_attribute: Attribute name in target entities to replace
        
    Returns:
        Modified to_entities list
        
    Raises:
        ValueError: If attributes don't exist in the entities
    """
    # Determine how many pairs we can process
    pairs_count = min(len(from_entities), len(to_entities))
    
    # Show length information
    if len(from_entities) != len(to_entities):
        print(f"ℹ️  List lengths differ: from_entities={len(from_entities)}, to_entities={len(to_entities)}")
        print(f"   Will process {pairs_count} pairs (shorter list determines count)")
        if len(from_entities) > len(to_entities):
            print(f"   {len(from_entities) - len(to_entities)} entities from source will be unused")
        else:
            print(f"   {len(to_entities) - len(from_entities)} entities in target will remain unchanged")
        print()
    
    # Validate that source entities have the from_attribute
    for i in range(pairs_count):
        if from_attribute not in from_entities[i]:
            raise ValueError(f"from_attribute '{from_attribute}' not found in from_entities[{i}]. Available attributes: {list(from_entities[i].keys())}")
    
    # Check if to_attribute exists in target entities
    missing_to_attribute = []
    for i in range(pairs_count):
        if to_attribute not in to_entities[i]:
            missing_to_attribute.append(i)
    
    # If to_attribute is missing, ask user if they want to add it
    if missing_to_attribute:
        print(f"⚠️  Attribute '{to_attribute}' not found in {len(missing_to_attribute)} target entities")
        print(f"   Missing in entities at indices: {missing_to_attribute}")
        print(f"   Available attributes in target entities: {list(to_entities[0].keys()) if to_entities else []}")
        print()
        
        response = input(f"Do you want to add '{to_attribute}' attribute to the target entities? (y/n): ").strip().lower()
        
        if response in ['y', 'yes']:
            print(f"✅ Adding '{to_attribute}' attribute to target entities...")
            # Add the missing attribute to all target entities (initialize with empty string)
            for entity in to_entities:
                if to_attribute not in entity:
                    entity[to_attribute] = ""
            print(f"   Added '{to_attribute}' attribute to {len([e for e in to_entities if to_attribute in e])} entities")
        else:
            print(f"❌ Cannot proceed without '{to_attribute}' attribute in target entities")
            raise ValueError(f"to_attribute '{to_attribute}' not found in target entities and user declined to add it")
    
    # Apply the values by zipping and replacing (only for the pairs we can process)
    modified_count = 0
    for i in range(pairs_count):
        from_entity = from_entities[i]
        to_entity = to_entities[i]
        
        old_value = to_entity[to_attribute]
        new_value = from_entity[from_attribute]
        
        if old_value != new_value:
            to_entity[to_attribute] = new_value
            modified_count += 1
            print(f"[{i+1}] '{to_attribute}': '{old_value}' → '{new_value}'")
        else:
            print(f"[{i+1}] '{to_attribute}': '{old_value}' (no change)")
    
    # Show summary including unprocessed entities
    if len(to_entities) > pairs_count:
        print(f"\n⏭️  {len(to_entities) - pairs_count} entities in target file were not modified (no corresponding source entity)")
    
    print(f"\n✅ Applied {modified_count} value changes out of {pairs_count} processed pairs")
    print(f"   Total entities in target file: {len(to_entities)}")
    return to_entities


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Apply values from one entities file to another by replacing attribute values",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python apply_value.py from.json to.json full_name "Customer Name"
  python apply_value.py source_entities.json target_entities.json email contact_email
        """
    )
    
    parser.add_argument('from_entities_file', 
                       help='JSON file containing source entities')
    parser.add_argument('to_entities_file',
                       help='JSON file containing target entities (will be modified)')
    parser.add_argument('from_attribute',
                       help='Attribute name in source entities to copy from')
    parser.add_argument('to_attribute', 
                       help='Attribute name in target entities to replace')
    
    args = parser.parse_args()
    
    try:
        # Load both entities files
        print(f"📂 Loading source entities from: {args.from_entities_file}")
        from_entities = load_entities_file(args.from_entities_file)
        print(f"   Loaded {len(from_entities)} entities")
        
        print(f"📂 Loading target entities from: {args.to_entities_file}")
        to_entities = load_entities_file(args.to_entities_file)
        print(f"   Loaded {len(to_entities)} entities")
        
        # Apply the values
        print(f"\n🔄 Applying '{args.from_attribute}' → '{args.to_attribute}':")
        print("-" * 60)
        
        modified_entities = apply_values(from_entities, to_entities, 
                                       args.from_attribute, args.to_attribute)
        
        # Save the modified entities back to file
        print(f"\n💾 Saving modified entities to: {args.to_entities_file}")
        save_entities_file(args.to_entities_file, modified_entities)
        
        print(f"✅ Successfully applied values from '{args.from_attribute}' to '{args.to_attribute}'")
        
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()