import os
import json
import fitz  # PyMuPDF
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 1. INITIALIZATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("[-] Missing GEMINI_API_KEY in your .env file.")

# Pointing to the specific discrepancy file provided for the assignment
PDF_PATH = os.path.join(BASE_DIR, 'data/WaiverPro-User-Guidelines-WITH-DISCREPANCIES.pdf')
OUTPUT_RULES_PATH = os.path.join(BASE_DIR, 'data/extracted_rules.json')

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# --- 2. TEXT EXTRACTION ---
def extract_text_from_pdf(pdf_path):
    print(f"[*] Reading PDF from {pdf_path}...")
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text += page.get_text("text") + "\n\n"
        print(f"[+] Successfully extracted {len(full_text)} characters of text.")
        return full_text
    except Exception as e:
        print(f"[-] Failed to read PDF: {e}")
        return None

# --- 3. AI EXTRACTION PIPELINE ---
def generate_rulebook(pdf_text):
    print("[*] Dispatching text to Gemini 3.1 Flash Lite for rule extraction...")
    
    # The Ultra-Lean Prompt
    prompt = f"""Extract every UI rule, label, and requirement from the text below.
Output ONLY a valid JSON array. No markdown, no conversational text.
Schema: [{{ "element": "element name", "rule": "exact requirement" }}]

TEXT:
{pdf_text}
"""
    
    try:
        # Using the Lite model to save quota, but maximizing the token output buffer
        completion = ai_client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0, # Absolute zero for strict extraction
                max_output_tokens=8192 # THE FIX: Prevent premature truncation of the JSON array
            ),
        )
        
        # Clean up potential markdown formatting just in case the model disobeys
        raw_response = completion.text.strip()
        if raw_response.startswith("```json"):
            raw_response = raw_response[7:-3].strip()
        elif raw_response.startswith("```"):
            raw_response = raw_response[3:-3].strip()
            
        rules_data = json.loads(raw_response)
        
        print(f"[+] Extracted {len(rules_data)} distinct UI rules.")
        
        # Save the brain
        os.makedirs(os.path.dirname(OUTPUT_RULES_PATH), exist_ok=True)
        with open(OUTPUT_RULES_PATH, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2)
            
        print(f"[+] Rulebook secured at: {OUTPUT_RULES_PATH}")
        
    except json.JSONDecodeError:
        print("[-] Fatal Error: The LLM failed to output valid JSON.")
        print(f"Raw Output:\n{completion.text}")
    except Exception as e:
        print(f"[-] Extraction failed: {e}")

if __name__ == "__main__":
    extracted_text = extract_text_from_pdf(PDF_PATH)
    if extracted_text:
        generate_rulebook(extracted_text)