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

"""
Hugging Face AI provider implementation.

This module implements the AIProvider interface for Hugging Face models
using the Hugging Face Inference API.
"""

import json
import re
import base64
from typing import Dict, List, Any, Optional
from io import BytesIO
import PIL.Image

from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError

from .base_provider import AIProvider, ProviderConfig
from config import LANGUAGE_CODES


class HuggingFaceProvider(AIProvider):
    """
    Hugging Face AI provider implementation.

    Supports text generation and vision capabilities through Hugging Face models.
    """

    def _validate_config(self) -> None:
        """Validate Hugging Face-specific configuration."""
        if not self.config.api_key:
            raise ValueError("HUGGINGFACE_API_KEY not found in configuration")

        # Set default model if not specified
        if not self.config.model_name:
            self.config.model_name = 'meta-llama/Meta-Llama-3-8B-Instruct'

        # Set default endpoint if not specified
        if not self.config.endpoint_url:
            self.config.endpoint_url = None  # Will use default HF endpoint

    def _initialize_client(self) -> None:
        """Initialize the Hugging Face client."""
        # Create InferenceClient with API key
        self.client = InferenceClient(
            model=self.config.model_name,
            token=self.config.api_key,
            base_url=self.config.endpoint_url
        )

        # Store model info for vision capability check
        self.is_vision_model = self._check_vision_capability()

        # Determine if model requires conversational API
        self.use_conversational = self._check_conversational_model()

    def _check_vision_capability(self) -> bool:
        """Check if the model supports vision capabilities."""
        # List of known vision-capable models (use lowercase for matching)
        vision_models = [
            'llava', 'idefics', 'vision', 'blip', 'clip', 'florence',
            'llama-3.2-11b-vision', 'llama-3.2-90b-vision',
            'qwen3-vl', 'qwen-vl', 'qwen2-vl'  # Qwen vision-language models
        ]

        if self.config.model_name:
            model_lower = self.config.model_name.lower()
            return any(vm in model_lower for vm in vision_models)
        return False

    def _check_conversational_model(self) -> bool:
        """Check if the model requires conversational API instead of text-generation."""
        # Models that require conversational API (use lowercase for matching)
        conversational_models = [
            'llama-3.2-11b-vision', 'llama-3.2-90b-vision',
            'llama-3-8b-instruct', 'llama-3-70b-instruct',
            'llama-2-', 'llama-3-',  # Most Llama models require conversational
            'llava', 'idefics', 'mistral-7b-instruct',
            'qwen3-vl', 'qwen-vl', 'qwen2-vl', 'qwen3-', 'qwen2-'  # Qwen models
        ]

        if self.config.model_name:
            model_lower = self.config.model_name.lower()
            return any(cm in model_lower for cm in conversational_models)
        return False

    def supports_vision(self) -> bool:
        """Check if the provider supports vision capabilities."""
        return self.is_vision_model

    def generate_bulk_entity_data(
        self,
        document_type: str,
        entity_fields: List[str],
        count: int,
        language: str = 'en'
    ) -> List[Dict[str, Any]]:
        """Generate bulk entity data using Hugging Face."""
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
                    # Generate content using appropriate API
                    if self.use_conversational:
                        # Use conversational API for vision models
                        messages = [{"role": "user", "content": prompt}]
                        response = self.client.chat_completion(
                            messages=messages,
                            max_tokens=self.config.max_tokens,
                            temperature=self.config.temperature,
                        )
                        # Extract text from chat response
                        response = response.choices[0].message.content
                    else:
                        # Use text_generation for regular models
                        response = self.client.text_generation(
                            prompt,
                            max_new_tokens=self.config.max_tokens,
                            temperature=self.config.temperature,
                            do_sample=True,
                        )

                    batch_entities = self._parse_entity_response(response, batch_size)

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
                except HfHubHTTPError as e:
                    print(f"❌ Hugging Face API Error in batch: {e} (retries left: {batch_retries})")
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
        """Generate HTML document using Hugging Face."""
        if template_image_path and not self.is_vision_model:
            print("⚠️  Template image provided but model doesn't support vision. Ignoring template.")
            template_image_path = None

        prompt = self._create_document_generation_prompt(
            document_type, entity_data, language, template_image_path, instructions
        )

        try:
            # Generate content using appropriate API
            if self.use_conversational:
                # Use conversational API for vision models
                messages = [{"role": "user", "content": prompt}]

                # Add image if provided and model supports vision
                if template_image_path and self.is_vision_model:
                    image = PIL.Image.open(template_image_path)
                    # Convert image to base64
                    buffered = BytesIO()
                    image.save(buffered, format="PNG")
                    image_base64 = base64.b64encode(buffered.getvalue()).decode()

                    # Add image to message (format depends on model)
                    # For now, we'll add it to the prompt text
                    messages[0]["content"] = f"[Image provided]\n\n{prompt}"

                response = self.client.chat_completion(
                    messages=messages,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
                # Extract text from chat response
                response = response.choices[0].message.content
            else:
                # Regular text generation for non-conversational models
                response = self.client.text_generation(
                    prompt,
                    max_new_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    do_sample=True,
                )

            # Clean up HTML content
            return self._clean_html_content(response)

        except HfHubHTTPError as e:
            if "safety" in str(e).lower() or "content" in str(e).lower():
                print("⚠️  Content blocked by safety filters, retrying with simplified prompt...")

                # Retry with simpler prompt
                simplified_prompt = f"""
                Create a simple HTML business document for: {document_type}
                Language: {language}
                Use this data: {json.dumps(entity_data, indent=2, ensure_ascii=False)}
                Keep content professional and appropriate.
                """

                if self.use_conversational:
                    messages = [{"role": "user", "content": simplified_prompt}]
                    response = self.client.chat_completion(
                        messages=messages,
                        max_tokens=self.config.max_tokens,
                        temperature=self.config.temperature,
                    )
                    response = response.choices[0].message.content
                else:
                    response = self.client.text_generation(
                        simplified_prompt,
                        max_new_tokens=self.config.max_tokens,
                        temperature=self.config.temperature,
                        do_sample=True,
                    )

                return self._clean_html_content(response)
            else:
                raise

    def analyze_document_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze document image using Hugging Face vision capabilities."""
        if not self.is_vision_model:
            raise NotImplementedError(
                f"Model '{self.config.model_name}' does not support vision capabilities. "
                "Please use a vision-capable model like 'meta-llama/Llama-3.2-11B-Vision-Instruct'."
            )

        try:
            image = PIL.Image.open(image_path)
        except Exception as e:
            raise ValueError(f"Error loading image: {e}")

        prompt = self._create_analysis_prompt()

        try:
            # Convert image to base64 for API
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Use appropriate API based on model type
            if self.use_conversational:
                messages = [{"role": "user", "content": prompt}]
                response = self.client.chat_completion(
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.3,  # Lower temperature for more consistent extraction
                )
                response = response.choices[0].message.content
            else:
                response = self.client.text_generation(
                    prompt,
                    max_new_tokens=1024,
                    temperature=0.3,  # Lower temperature for more consistent extraction
                    do_sample=True,
                )

            response_text = response.strip()

            # Clean and parse response
            response_text = self._clean_json_response(response_text)
            analysis_result = json.loads(response_text)

            # Validate required fields
            self._validate_analysis_result(analysis_result)

            return analysis_result

        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            return self._create_error_analysis_result(str(e), response if 'response' in locals() else "")
        except Exception as e:
            return self._create_error_analysis_result(str(e))

    # Private helper methods

    def _create_entity_generation_prompt(
        self, document_type: str, entity_fields: List[str],
        batch_size: int, language_name: str, language: str
    ) -> str:
        """Create prompt for entity generation."""
        return f"""You are a helpful assistant that generates realistic business data.

Create realistic business data for: {document_type}

REQUIREMENT: Generate EXACTLY {batch_size} data records

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

CRITICAL: Return ONLY a valid JSON array with EXACTLY {batch_size} objects. Do not include any markdown formatting, explanations, or extra text. Just the raw JSON array.

Example format:
[
  {{
    "field1": "value1",
    "field2": "value2"
  }},
  ...
]"""

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

        return f"""You are a professional document generator.

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
- Use professional styling with inline CSS
- Return ONLY the HTML content without any markdown formatting or code blocks
- Start directly with <!DOCTYPE html> or <html>
{additional_instructions}

Generate the complete HTML document now:"""

    def _create_analysis_prompt(self) -> str:
        """Create prompt for document analysis."""
        return """Analyze this document image and extract the following information:
1. Document Type (e.g., invoice, receipt, contract, etc.)
2. Language Detection (detect the primary language used)
3. Entity Extraction (extract all relevant information like names, addresses, amounts, dates, etc.)

Return ALL extracted text in the SAME LANGUAGE as detected in the document.

Return the results in this exact JSON format:
{
  "document_type": "type in detected language",
  "detected_language": "language code (e.g., 'en', 'es', 'fr')",
  "confidence": "high/medium/low",
  "extracted_entities": {
    "entity_name": "value",
    "another_entity": "value"
  }
}

Return ONLY the JSON object - no explanations, no markdown formatting, just the raw JSON."""

    def _parse_entity_response(self, response_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """Parse entity generation response."""
        response_text = response_text.strip()

        # Clean up response - remove markdown formatting if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        # Find JSON array in response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)

        response_text = response_text.strip()

        try:
            data = json.loads(response_text)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            # Try to extract JSON objects manually
            objects = []
            for match in re.finditer(r'\{[^{}]*\}', response_text):
                try:
                    obj = json.loads(match.group(0))
                    objects.append(obj)
                except:
                    pass
            return objects

    def _clean_html_content(self, html_content: str) -> str:
        """Clean HTML content from markdown formatting."""
        # Remove markdown code blocks
        if html_content.startswith('```html'):
            html_content = html_content[7:]
        if html_content.startswith('```'):
            html_content = html_content[3:]
        if html_content.endswith('```'):
            html_content = html_content[:-3]

        # Find HTML content
        html_match = re.search(r'<!DOCTYPE.*?</html>', html_content, re.DOTALL | re.IGNORECASE)
        if html_match:
            return html_match.group(0).strip()

        # Try to find just the HTML tag content
        html_match = re.search(r'<html.*?</html>', html_content, re.DOTALL | re.IGNORECASE)
        if html_match:
            return f"<!DOCTYPE html>\n{html_match.group(0).strip()}"

        return html_content.strip()

    def _clean_json_response(self, response_text: str) -> str:
        """Clean JSON response from markdown formatting."""
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        # Try to find JSON object in response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)

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