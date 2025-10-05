"""
Google Gemini AI provider implementation.

This module implements the AIProvider interface for Google's Gemini models.
"""

import google.generativeai as genai
import json
import re
from typing import Dict, List, Any, Optional
import PIL.Image

from .base_provider import AIProvider, ProviderConfig
from config import LANGUAGE_CODES


class GeminiProvider(AIProvider):
    """
    Google Gemini AI provider implementation.

    Supports text generation and vision capabilities through Gemini models.
    """

    def _validate_config(self) -> None:
        """Validate Gemini-specific configuration."""
        if not self.config.api_key:
            raise ValueError("GEMINI_API_KEY not found in configuration")

        # Set default model if not specified
        if not self.config.model_name:
            self.config.model_name = 'gemini-2.5-flash'

    def _initialize_client(self) -> None:
        """Initialize the Gemini client."""
        genai.configure(api_key=self.config.api_key)

        # Configure safety settings
        safety_settings = self.config.safety_settings or [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            }
        ]

        self.model = genai.GenerativeModel(
            self.config.model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            ),
            safety_settings=safety_settings
        )

    def supports_vision(self) -> bool:
        """Gemini models support vision capabilities."""
        return True

    def generate_bulk_entity_data(
        self,
        document_type: str,
        entity_fields: List[str],
        count: int,
        language: str = 'en'
    ) -> List[Dict[str, Any]]:
        """Generate bulk entity data using Gemini."""
        # Validate language code
        if language not in LANGUAGE_CODES:
            raise ValueError(f"Unsupported language code: '{language}'. Supported codes: {', '.join(sorted(LANGUAGE_CODES.keys()))}")

        language_context = LANGUAGE_CODES[language]
        language_name = language_context.replace(' context', '')

        # Generate entity data with retry logic
        max_batch_retries = 5
        entity_list = []
        remaining_count = count

        while remaining_count > 0 and max_batch_retries > 0:
            batch_retries = 3
            batch_size = min(remaining_count, 5)  # Generate max 5 at a time

            prompt = self._create_entity_generation_prompt(
                document_type, entity_fields, batch_size, language_name, language
            )

            batch_success = False

            while batch_retries > 0 and not batch_success:
                try:
                    response = self.model.generate_content(prompt)
                    batch_entities = self._parse_entity_response(response.text, batch_size)

                    if len(batch_entities) == batch_size:
                        # Add metadata to each entity record
                        for entity in batch_entities:
                            entity['_document_type'] = document_type
                            entity['_language'] = language

                        entity_list.extend(batch_entities)
                        remaining_count -= batch_size
                        print(f"✅ Generated batch of {len(batch_entities)} entities ({len(entity_list)}/{count} total)")
                        batch_success = True
                    elif len(batch_entities) > 0:
                        # Accept partial results
                        actual_count = min(len(batch_entities), batch_size)
                        useful_entities = batch_entities[:actual_count]

                        for entity in useful_entities:
                            entity['_document_type'] = document_type
                            entity['_language'] = language

                        entity_list.extend(useful_entities)
                        remaining_count -= len(useful_entities)
                        print(f"⚠️  Expected {batch_size} entities but got {len(batch_entities)}, accepting {len(useful_entities)}")
                        batch_success = True
                    else:
                        print(f"❌ Got empty response, retrying batch ({batch_retries} retries left)")
                        batch_retries -= 1

                except json.JSONDecodeError as e:
                    print(f"❌ JSON Parse Error in batch: {e} (retries left: {batch_retries})")
                    batch_retries -= 1
                except Exception as e:
                    print(f"❌ API Error in batch: {e} (retries left: {batch_retries})")
                    batch_retries -= 1

            if not batch_success:
                max_batch_retries -= 1
                print(f"❌ Batch failed completely, reducing overall retries to {max_batch_retries}")

        # Fill remaining slots if necessary
        if len(entity_list) < count:
            print(f"⚠️  Only generated {len(entity_list)}/{count} entities after retries")
            self._fill_remaining_entities(entity_list, entity_fields, document_type, language, count)

        print(f"✅ Successfully generated {len(entity_list)} entity records")
        return entity_list[:count]

    def generate_document_with_data(
        self,
        document_type: str,
        entity_data: Dict[str, str],
        language: str = 'en',
        template_image_path: Optional[str] = None,
        instructions: Optional[str] = None
    ) -> str:
        """Generate HTML document using Gemini."""
        prompt = self._create_document_generation_prompt(
            document_type, entity_data, language, template_image_path, instructions
        )

        # Generate content with or without template image
        if template_image_path:
            try:
                image = PIL.Image.open(template_image_path)
                response = self.model.generate_content([prompt, image])
            except Exception as e:
                raise ValueError(f"Error loading template image: {e}")
        else:
            response = self.model.generate_content(prompt)

        # Handle safety filters
        html_content = self._handle_generation_response(
            response, document_type, entity_data, language
        )

        # Clean up HTML content
        return self._clean_html_content(html_content)

    def analyze_document_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze document image using Gemini vision capabilities."""
        try:
            image = PIL.Image.open(image_path)
        except Exception as e:
            raise ValueError(f"Error loading image: {e}")

        prompt = self._create_analysis_prompt()

        try:
            response = self.model.generate_content([prompt, image])
            response_text = response.text.strip()

            # Clean and parse response
            response_text = self._clean_json_response(response_text)
            analysis_result = json.loads(response_text)

            # Validate required fields
            self._validate_analysis_result(analysis_result)

            return analysis_result

        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            return self._create_error_analysis_result(str(e), response.text if 'response' in locals() else "")
        except Exception as e:
            return self._create_error_analysis_result(str(e))

    # Private helper methods

    def _create_entity_generation_prompt(
        self, document_type: str, entity_fields: List[str],
        batch_size: int, language_name: str, language: str
    ) -> str:
        """Create prompt for entity generation."""
        return f"""Create realistic business data for: {document_type}

🎯 ABSOLUTE REQUIREMENT: Generate EXACTLY {batch_size} data records

MANDATORY FIELD STRUCTURE:
- Each record MUST have ALL {len(entity_fields)} fields: {', '.join(entity_fields)}
- NO missing fields, NO extra fields, NO null values
- ALL text content must be written in {language_name} language

Data Requirements:
- Make company names realistic for this business type in {language_name}-speaking regions
- Use real-sounding names and addresses appropriate for {language_name} culture
- Generate realistic amounts with appropriate currency symbols for the region
- Each record must be unique and different
- ALL descriptive text must be written in {language_name}

CRITICAL: Return ONLY a JSON array with EXACTLY {batch_size} objects, no extra text or formatting."""

    def _create_document_generation_prompt(
        self, document_type: str, entity_data: Dict[str, str],
        language: str, template_image_path: Optional[str], instructions: Optional[str]
    ) -> str:
        """Create prompt for document generation."""
        template_instruction = ""
        if template_image_path:
            template_instruction = """
        CRITICAL TEMPLATE REQUIREMENT - EXACT LAYOUT MATCHING:
        - You MUST match the general layout and appearance of the provided document image
        - ANALYZE the template image carefully and replicate the structure
        - NEVER use any personal information from the template image
        - Only replicate the LAYOUT, STRUCTURE, and VISUAL DESIGN
        """

        additional_instructions = ""
        if instructions:
            additional_instructions = f"""

        ADDITIONAL INSTRUCTIONS:
        {instructions}
        """

        return f"""
        Create an HTML business document for: {document_type}
        {template_instruction}
        Language: {language}

        Entity Data to Use:
        {json.dumps(entity_data, indent=2, ensure_ascii=False)}

        Requirements:
        - Use the EXACT entity data provided above
        - Generate the ENTIRE DOCUMENT in {language} language
        - Create a completed, filled-out document (not a fillable form)
        - Design for printing on 8.5" x 11" Letter-size paper
        - Use professional styling with CSS
        - Return only HTML content without markdown formatting
        {additional_instructions}
        """

    def _create_analysis_prompt(self) -> str:
        """Create prompt for document analysis."""
        return """
        Analyze this document image and extract:
        1. Document Type
        2. Language Detection
        3. Entity Extraction (names, addresses, amounts, etc.)

        Return ALL extracted text in the SAME LANGUAGE as detected in the document.

        Return results in JSON format:
        {
          "document_type": "type in detected language",
          "detected_language": "language code",
          "confidence": "high/medium/low",
          "extracted_entities": {
            "entity_name": "value"
          }
        }

        Return ONLY the JSON - no explanations.
        """

    def _parse_entity_response(self, response_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """Parse entity generation response."""
        response_text = response_text.strip()

        # Clean up response
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        # Find JSON array
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)

        response_text = response_text.strip()

        data = json.loads(response_text)
        return data if isinstance(data, list) else [data]

    def _handle_generation_response(
        self, response: Any, document_type: str,
        entity_data: Dict[str, str], language: str
    ) -> str:
        """Handle response from document generation, including safety filters."""
        if not response.parts:
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                finish_reason = candidate.finish_reason

                if finish_reason == 2:  # SAFETY
                    print("⚠️  Content blocked by safety filters, retrying with simplified prompt...")

                    # Retry with simpler prompt
                    simplified_prompt = f"""
                    Create a simple HTML business document for: {document_type}
                    Language: {language}
                    Use this data: {json.dumps(entity_data, indent=2, ensure_ascii=False)}
                    Keep content professional and appropriate.
                    """

                    response = self.model.generate_content(simplified_prompt)

                    if not response.parts:
                        raise ValueError(f"Content generation failed after retry. Try simpler content.")
                else:
                    raise ValueError(f"Content generation failed. Finish reason: {finish_reason}")
            else:
                raise ValueError("No response content generated.")

        return response.text.strip()

    def _clean_html_content(self, html_content: str) -> str:
        """Clean HTML content from markdown formatting."""
        if html_content.startswith('```html'):
            html_content = html_content[7:]
        if html_content.startswith('```'):
            html_content = html_content[3:]
        if html_content.endswith('```'):
            html_content = html_content[:-3]
        return html_content.strip()

    def _clean_json_response(self, response_text: str) -> str:
        """Clean JSON response from markdown formatting."""
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        return response_text.strip()

    def _validate_analysis_result(self, result: Dict[str, Any]) -> None:
        """Validate document analysis result."""
        required_fields = ['document_type', 'detected_language', 'extracted_entities']
        for field in required_fields:
            if field not in result:
                result[field] = "Unknown" if field != 'extracted_entities' else {}

    def _create_error_analysis_result(self, error: str, raw_response: str = "") -> Dict[str, Any]:
        """Create error result for document analysis."""
        return {
            "document_type": "Analysis Failed",
            "detected_language": "unknown",
            "confidence": "low",
            "extracted_entities": {},
            "error": error,
            "raw_response": raw_response
        }

    def _fill_remaining_entities(
        self, entity_list: List[Dict[str, Any]], entity_fields: List[str],
        document_type: str, language: str, target_count: int
    ) -> None:
        """Fill remaining entity slots with fallback data."""
        remaining = target_count - len(entity_list)
        for i in range(remaining):
            entity = {field: f"generated_{field}_{len(entity_list) + i + 1}" for field in entity_fields}
            entity['_document_type'] = document_type
            entity['_language'] = language
            entity_list.append(entity)