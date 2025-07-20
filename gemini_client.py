import google.generativeai as genai
import json
from typing import Dict, List, Any
from config import GEMINI_API_KEY, LANGUAGE_CODES

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=8192,
            )
        )
    
    def generate_bulk_entity_data(self, document_type: str, entity_fields: List[str], count: int, language: str = 'en') -> List[Dict[str, Any]]:
        # Validate language code
        if language not in LANGUAGE_CODES:
            raise ValueError(f"Unsupported language code: '{language}'. Supported codes: {', '.join(sorted(LANGUAGE_CODES.keys()))}")
        
        language_context = LANGUAGE_CODES[language]
        
        # Get language name for clearer instructions
        language_name = language_context.replace(' context', '')
        
        prompt = f"""Create realistic business data for: {document_type}

Generate {count} data records with these fields: {', '.join(entity_fields)}

CRITICAL LANGUAGE REQUIREMENT:
- ALL text content must be written in {language_name} language
- ALL field values including descriptions, terms, conditions, notes, etc. must be in {language_name}
- Company names, addresses, and person names should be culturally appropriate for {language_name}-speaking regions
- Do NOT mix languages - everything must be consistently in {language_name}

Data Requirements:
- Make company names realistic for this business type in {language_name}-speaking regions
- Use real-sounding names and addresses appropriate for {language_name} culture
- Generate realistic amounts with appropriate currency symbols for the region
- Generate realistic dates using region-specific formats:
  * Thai (th): Use Buddhist Era dates (BE) - add 543 years to AD dates (e.g., "15 มกราคม 2567" for January 15, 2024)
  * German (de): Use DD.MM.YYYY format (e.g., "15.01.2024")
  * French (fr): Use DD/MM/YYYY format (e.g., "15/01/2024")
  * Japanese (ja): Use Japanese era dates when appropriate (e.g., "令和6年1月15日")
  * Chinese (zh): Use YYYY年MM月DD日 format (e.g., "2024年1月15日")
  * Korean (ko): Use YYYY년 MM월 DD일 format (e.g., "2024년 1월 15일")
  * Arabic (ar): Use Arabic calendar dates when appropriate
  * English (en): Use MM/DD/YYYY format (e.g., "01/15/2024")
  * Spanish (es): Use DD/MM/YYYY format (e.g., "15/01/2024")
  * Portuguese (pt): Use DD/MM/YYYY format (e.g., "15/01/2024")
  * Russian (ru): Use DD.MM.YYYY format (e.g., "15.01.2024")
  * Italian (it): Use DD/MM/YYYY format (e.g., "15/01/2024")
  * Dutch (nl): Use DD-MM-YYYY format (e.g., "15-01-2024")
  * For other languages: Use the standard regional date format for that country/culture
- Generate email addresses using region-appropriate domains:
  * Thai (th): Use .co.th, .ac.th, or popular Thai domains like @hotmail.co.th, @gmail.com
  * German (de): Use .de domains like @web.de, @gmx.de, @t-online.de, @gmail.com
  * French (fr): Use .fr domains like @orange.fr, @free.fr, @laposte.net, @gmail.com
  * Japanese (ja): Use .jp domains like @yahoo.co.jp, @gmail.com, @hotmail.co.jp
  * Chinese (zh): Use .cn domains like @qq.com, @163.com, @126.com, @sina.com
  * Korean (ko): Use .kr domains like @naver.com, @daum.net, @gmail.com, @hanmail.net
  * Spanish (es): Use .es domains like @hotmail.es, @gmail.com, @yahoo.es
  * Portuguese (pt): Use .pt or .br domains like @sapo.pt, @gmail.com, @hotmail.com, @uol.com.br
  * Russian (ru): Use .ru domains like @mail.ru, @yandex.ru, @gmail.com, @rambler.ru
  * Italian (it): Use .it domains like @libero.it, @gmail.com, @hotmail.it, @alice.it
  * Dutch (nl): Use .nl domains like @ziggo.nl, @gmail.com, @hotmail.nl, @xs4all.nl
  * Arabic (ar): Use appropriate regional domains (.sa, .ae, .eg, etc.) or @gmail.com
  * English (en): Use .com domains like @gmail.com, @yahoo.com, @hotmail.com, @outlook.com
  * For other languages: Use the most common email domains for that country/region
- Each record must be unique and different
- ALL descriptive text (terms, conditions, notes, descriptions) must be written in {language_name}

Examples of language consistency:
- German (de): "50/50 Gewinnaufteilung, gleiche Managementverantwortlichkeiten"
- Spanish (es): "División de ganancias 50/50, responsabilidades de gestión iguales"  
- French (fr): "Partage des bénéfices 50/50, responsabilités de gestion égales"
- Japanese (ja): "50/50利益分配、平等な経営責任"

Return ONLY a JSON array with no extra text or formatting:
[{{"field1": "realistic_value1", "field2": "realistic_value2"}}, {{"field1": "realistic_value3", "field2": "realistic_value4"}}]"""
        
        response = self.model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up the response text - remove markdown formatting and explanations
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith('```'):
            response_text = response_text[3:]   # Remove just ```
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # Remove closing ```
        
        # Find JSON array in the response
        import re
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        response_text = response_text.strip()
        
        try:
            data = json.loads(response_text)
            # Ensure we return a list
            if isinstance(data, list):
                entity_list = data
            else:
                # If single object returned, wrap in list
                entity_list = [data]
            
            # Add document_type to each entity record
            for entity in entity_list:
                entity['_document_type'] = document_type
                entity['_language'] = language
            
            print(f"Successfully generated {len(entity_list)} entity records")
            return entity_list
            
        except json.JSONDecodeError as e:
            # Print debug information
            print(f"❌ JSON Parse Error: {e}")
            print(f"📏 Raw response length: {len(response.text)}")
            print(f"📝 Full raw response:")
            print("-" * 50)
            print(response.text)
            print("-" * 50)
            print(f"🧹 Cleaned response length: {len(response_text)}")
            print(f"🧹 Cleaned response:")
            print("-" * 50)
            print(response_text)
            print("-" * 50)
            
            # Try to provide helpful error message
            if "sample_" in response_text.lower() or not response_text.startswith('['):
                print("⚠️  It looks like the LLM didn't generate proper JSON or returned sample data")
                print("💡 This might be due to:")
                print("   - API key issues")
                print("   - Model not understanding the prompt") 
                print("   - Response filtering/safety controls")
            
            # Fallback if response isn't valid JSON
            print("🔄 Falling back to sample data due to JSON parse error")
            fallback_data = []
            for i in range(count):
                entity = {field: f"sample_{field}_{i+1}" for field in entity_fields}
                entity['_document_type'] = document_type
                entity['_language'] = language
                fallback_data.append(entity)
            return fallback_data
    
    def generate_document_with_data(self, document_type: str, entity_data: Dict[str, str], language: str = 'en') -> str:
        prompt = f"""
        Based on the following description, create an HTML-based business form that is already prefilled with synthetic, realistic data. Do NOT create a fillable form - create a completed form document that looks like it has been filled out already.

        Description: {document_type}

        Language and Localization: {language}
        
        Entity Data to Use:
        {json.dumps(entity_data, indent=2, ensure_ascii=False)}
        
        CRITICAL LANGUAGE REQUIREMENTS:
        - Use the EXACT entity data provided above - do not generate new data, use these specific values
        - Generate the ENTIRE DOCUMENT in {language} language
        - ALL text content must be written in {language} - including headers, labels, descriptions, terms, conditions, and any filler text
        - NEVER use Lorem Ipsum or placeholder text in Latin or any other language
        - NEVER mix languages - everything must be consistently in {language}
        - ALL descriptive content, legal text, terms and conditions, and additional information must be written in proper {language}
        - Do NOT use English text anywhere in the document when {language} is not English
        - Use realistic synthetic data appropriate for {language}-speaking countries, including:
          * Company/business names that sound natural in {language}-speaking regions
          * Personal names common in {language}-speaking regions
          * Business addresses with proper formatting for {language}-speaking countries (street addresses, cities, states/provinces, postal codes)
          * Personal addresses with proper formatting for {language}-speaking countries
          * Phone numbers in the correct format for {language}-speaking countries
          * Email addresses with appropriate domains
          * Monetary amounts in the correct currency and format for {language}-speaking countries
          * Date formats standard in {language}-speaking countries
          * ID numbers, postal codes, and other regional identifiers appropriate for the region
        - DO NOT include any logo images, SVG graphics, or image elements - these cause PDF conversion issues
        - Instead of logos, use styled text headers with company names and attractive typography
        - Use RICH and ATTRACTIVE styling with inline CSS and embedded styles - make it visually appealing with colors, gradients, shadows, and modern design elements
        - Include advanced layout techniques like CSS Grid, Flexbox, colored headers, branded sections, and professional color schemes
        - Use attractive typography with varied font sizes, weights, and colors to create visual hierarchy
        - CRITICAL: Include proper charset declaration and Unicode-safe fonts for international characters
        - Use font families that support international characters: Arial, 'Segoe UI', 'DejaVu Sans', sans-serif
        - Add visual elements like colored backgrounds, borders, subtle shadows, and modern spacing
        - Make it look like a premium, professionally designed business document with rich visual appeal
        - Use semantic HTML elements (headings, paragraphs, tables, etc.) but style them beautifully
        - Include company branding elements like colored headers and branded color schemes (NO logos or images)
        - CRITICAL: NEVER use white backgrounds anywhere in the document (background: white, background-color: white, background: #ffffff, background-color: #ffffff, or any white color variations)
        - CRITICAL: Do NOT include html, head, body tags - return only the content that goes inside a body tag
        - IMPORTANT: Include a style tag at the beginning with UTF-8 safe font declarations
        - CRITICAL: Do NOT set any background on the body element or root container - keep all backgrounds transparent
        - ALL backgrounds must be either transparent or semi-transparent to allow the paper texture to show through
        - Main document container: Use transparent backgrounds (background: transparent or background-color: transparent)
        - Headers, sections, boxes, tables, divs: Use semi-transparent backgrounds with rgba() values only
        - CRITICAL: Do NOT use any colored backgrounds anywhere in the document
        - FORBIDDEN: Any background colors including rgba(), rgb(), or named colors on any elements
        - FORBIDDEN: background-color properties on any HTML elements (divs, sections, headers, tables, etc.)
        - Use only transparent backgrounds: background: transparent or no background styling at all
        - Create visual separation through borders, spacing, typography, and layout instead of background colors
        - Use subtle borders (1px solid #ddd), padding, margins, and typography hierarchy for visual organization
        - Text contrast should come from dark text colors (#333, #000) on the transparent/paper background only
        - CRITICAL: This form MUST be designed for PRINTING on exactly 8.5" x 11" Letter-size paper, NOT for online use
        - MANDATORY: Set the document container to EXACTLY 8.5 inches wide by 11 inches tall using CSS:
          * width: 8.5in; height: 11in; (or width: 612px; height: 792px; at 72 DPI)
          * Use CSS @media print rules to ensure proper printing dimensions
          * Add: @media print {{ @page {{ size: letter; margin: 0; }} }}
        - CRITICAL: Set NO print margins to allow background to extend to page edges
        - CRITICAL: Use margin: 0 in @page to eliminate white borders in PDF
        - This gives you the full content area of exactly 8.5" wide x 11" tall to work with
        - Add internal padding to the main container for text readability (e.g., padding: 0.3in)
        - CRITICAL: Generate VERBOSE, TEXT-RICH documents with comprehensive content suitable for the document type
        - MANDATORY: Fill the ENTIRE available content area (7.5" x 10") from top to bottom with detailed text content
        - CRITICAL: Include at least 2-3 paragraphs of standard text relevant to each document type:
          * Medical forms: Patient rights, treatment consent, privacy policies, medical history importance, healthcare provider responsibilities
          * Contracts: Terms of agreement, payment conditions, dispute resolution, termination clauses, liability limitations
          * Invoices: Payment terms, late fees, service descriptions, delivery conditions, warranty information
          * Rental agreements: Tenant responsibilities, property maintenance, lease terms, security deposit policies, eviction procedures
          * Insurance forms: Coverage details, claim procedures, exclusions, premium payment terms, policyholder obligations
          * Employment documents: Job responsibilities, compensation details, benefits information, termination policies, confidentiality requirements
        - MANDATORY: Use smaller font sizes to accommodate increased text volume:
          * Main body text: font-size: 11px or 12px (instead of default 14px-16px)
          * Headers: font-size: 16px-18px (h1), 14px-16px (h2), 12px-14px (h3)
          * Legal/disclaimer text: font-size: 9px-10px
          * Table text: font-size: 10px-11px
          * This allows for significantly more content while maintaining readability
        - Include extensive sections with detailed explanations, comprehensive terms and conditions, legal clauses, and thorough descriptions
        - Add multiple paragraphs of relevant text for each section - do NOT create sparse or minimal content
        - For contracts/agreements: Include detailed legal language, comprehensive terms, conditions, rights, obligations, and procedures
        - For invoices: Include detailed service descriptions, comprehensive terms of payment, delivery conditions, and additional clauses
        - For reports: Include thorough analysis, detailed findings, comprehensive recommendations, and extensive explanations
        - Use appropriate spacing and layout but prioritize CONTENT DENSITY over white space
        - Each section should contain multiple sentences and paragraphs of relevant, professional text
        - Generate realistic, detailed content that professionals would expect to see in this type of document
        - The document should appear substantial, comprehensive, and professionally complete
        - CRITICAL: Include region-specific legal disclosures, warnings, and standard text relevant to the document type
        - MANDATORY: Add legal text in smaller font (font-size: 0.8em or 0.9em) that references actual laws/regulations for the language region:
          * Thai (th): Reference Thai Personal Data Protection Act (PDPA), Consumer Protection Act, or relevant Thai commercial law
          * German (de): Reference DSGVO/GDPR, BGB (German Civil Code), or relevant German commercial regulations
          * French (fr): Reference RGPD, Code Civil, Code de Commerce, or relevant French legal frameworks
          * Japanese (ja): Reference Personal Information Protection Law, Civil Code, or relevant Japanese regulations
          * Chinese (zh): Reference Cybersecurity Law, Consumer Protection Law, or relevant Chinese regulations
          * Korean (ko): Reference Personal Information Protection Act, Consumer Protection Act, or Korean commercial law
          * Spanish (es): Reference LOPD-GDD, Código Civil, or relevant Spanish legal frameworks
          * Portuguese (pt): Reference LGPD (Brazil) or Portuguese data protection laws as appropriate
          * Russian (ru): Reference Federal Law on Personal Data, Consumer Protection Law, or relevant Russian regulations
          * Italian (it): Reference GDPR implementation, Codice Civile, or relevant Italian legal frameworks
          * Dutch (nl): Reference AVG/GDPR, Burgerlijk Wetboek, or relevant Dutch legal frameworks
          * Arabic (ar): Reference appropriate regional privacy/commercial laws based on country context
          * English (en): Reference US state laws based on addresses in entity data (e.g., California CCPA, Texas Business Code, etc.)
        - Include realistic legal disclaimers, privacy notices, terms of service, or regulatory compliance statements
        - Add professional footer text with relevant legal references and compliance information
        - Legal text should be contextually appropriate for the specific document type (medical forms = HIPAA/privacy, contracts = commercial law, etc.)
        - MANDATORY: Include CSS that prevents page breaks and ensures single-page printing:
          * page-break-inside: avoid; page-break-after: avoid; page-break-before: avoid;
        - Use print-friendly styling with exact measurements that will look professional when printed on paper
        - IMPORTANT: This is a PRINT document - optimize for physical paper printing with exact dimensions, not web display
        - Do NOT include any input fields - this should be a completed, read-only document
        - Return only the HTML code without any markdown formatting or explanations

        The form should look like a high-end, visually rich business document designed for printing on Letter-size paper that has been completed and could be printed as a final document. Make it stand out with attractive colors, modern layout, and professional design elements while ensuring it fits properly on a single printed page. All content, labels, and data should be culturally and linguistically appropriate for {language}-speaking regions.
        
        LANGUAGE CONSISTENCY EXAMPLES:
        - German document should have terms like: "Geschäftsbedingungen", "Zahlungsbedingungen", "Vertragsdauer", "Unterschrift", "Datum", not Lorem Ipsum
        - Spanish document should have terms like: "Términos y Condiciones", "Condiciones de Pago", "Duración del Contrato", "Firma", "Fecha"
        - French document should have terms like: "Termes et Conditions", "Conditions de Paiement", "Durée du Contrat", "Signature", "Date"
        - Japanese document should have terms like: "利用規約", "支払い条件", "契約期間", "署名", "日付"
        
        FORBIDDEN CONTENT:
        - NO Lorem Ipsum text (Lorem ipsum dolor sit amet, consectetur adipiscing elit...)
        - NO placeholder text in Latin or English when {language} is not English
        - NO mixed language content
        - NO logo images, SVG graphics, or any image elements (img, svg, object, embed tags)
        - NO external image references or base64 encoded images
        - All filler text and descriptions must be meaningful and in {language}
        
        CRITICAL ENTITY DATA REQUIREMENTS:
        - MUST use ALL the provided entity data exactly as specified in the Entity Data section above
        - Place each entity field naturally within the document structure where it makes sense
        - Do NOT generate new values - use the exact values provided in the entity data
        - Ensure the document incorporates all the entity fields and values provided
        - Write ALL additional content (headers, labels, legal text, descriptions) in {language}
        """
        
        response = self.model.generate_content(prompt)
        html_content = response.text.strip()
        
        # Remove markdown code blocks if present
        if html_content.startswith('```html'):
            html_content = html_content[7:]  # Remove ```html
        if html_content.startswith('```'):
            html_content = html_content[3:]   # Remove just ```
        if html_content.endswith('```'):
            html_content = html_content[:-3]  # Remove closing ```
        
        return html_content.strip()