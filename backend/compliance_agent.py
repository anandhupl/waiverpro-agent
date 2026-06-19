import os
import json
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types
from pydantic import BaseModel
from PIL import Image, ImageDraw

# --- 1. INITIALIZATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, '.env')

print(f"[*] Force-loading environment from: {env_path}")
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not GEMINI_API_KEY:
    raise ValueError("[-] Missing required environment variables (.env).")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

print("[*] Booting up local SentenceTransformer for Retrieval...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# --- 2. STRUCTURED OUTPUT SCHEMA ---
class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class ComplianceReport(BaseModel):
    is_compliant: bool
    reasoning: str
    element_found: bool
    bounding_box: BoundingBox | None

# --- 3. THE AGENT LOGIC ---
def run_compliance_check(rule_text, search_query, screenshot_path):
    """
    Queries Supabase for the UI element and asks Gemini if it complies with the rule.
    Returns a dictionary of the results for the orchestrator to aggregate.
    """
    print(f"\n[*] Evaluating Rule: '{rule_text}'")
    
    query_vector = embedder.encode(search_query).tolist()
    
    response = supabase.rpc(
        "match_dom_elements",
        {
            "query_embedding": query_vector, 
            "match_threshold": 0.15, 
            "match_count": 30
        }
    ).execute()
    
    results = response.data
    if not results:
        print("[-] No relevant UI elements found in the database.")
        return {"rule": rule_text, "status": "Error: Element not found in DOM"}

    # Lean context string
    context_string = "\n".join([f"- {match['content']}" for match in results])
    
    # THE LEAN PROMPT: Stripped of persona, completely literal.
    prompt = f"""
Rule: "{rule_text}"
Extracted UI Elements:
{context_string}

Task: Evaluate if the UI Elements satisfy the Rule. 
If yes: is_compliant = true.
If no: is_compliant = false, element_found = true, and extract bounding_box coordinates.
"""
    
    print("[*] Dispatching lean prompt to Gemini...")
    
    # --- The Exponential Backoff Retry Loop ---
    max_retries = 4
    base_wait = 15

    for attempt in range(max_retries):
        try:
            # Using 2.5-flash for the strict reasoning
            completion = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ComplianceReport,
                    temperature=0.0 # Zero variance
                ),
            )
            
            report_data = json.loads(completion.text)
            
            print(f"[+] Compliant: {report_data['is_compliant']} | Reason: {report_data['reasoning']}")
            
            # Handle visual evidence generation
            evidence_path = None
            if report_data['element_found'] and not report_data['is_compliant'] and report_data.get('bounding_box'):
                bbox = report_data['bounding_box']
                try:
                    img = Image.open(screenshot_path)
                    draw = ImageDraw.Draw(img)
                    
                    x0, y0 = bbox['x'], bbox['y']
                    x1, y1 = x0 + bbox['width'], y0 + bbox['height']
                    
                    draw.rectangle([x0, y0, x1, y1], outline="red", width=6)
                    
                    # Generate a unique filename based on the rule (simplified)
                    safe_rule_name = "".join(x for x in rule_text[:15] if x.isalnum())
                    evidence_path = os.path.join(BASE_DIR, f"data/screenshots/violation_{safe_rule_name}.png")
                    
                    img.save(evidence_path)
                    print(f"[!] Violation evidence secured: {evidence_path}")
                    
                except FileNotFoundError:
                    print(f"[-] Could not find screenshot at {screenshot_path}")

            # Return structured data for the orchestrator
            return {
                "rule": rule_text,
                "is_compliant": report_data['is_compliant'],
                "reasoning": report_data['reasoning'],
                "evidence_path": evidence_path
            }

        except Exception as e:
            error_msg = str(e)
            
            # Catch server overloads (503) and rate limits (429)
            if "503" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = base_wait * (2 ** attempt) # Calculates: 15s, 30s, 60s
                    print(f"\n[-] Google API slammed (503/429). Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print("\n[-] Max retries reached. The free-tier servers are completely jammed. Skipping rule.")
                    return None
            else:
                # If it's a completely different error (like a bad prompt or missing image), crash gracefully
                print(f"\n[-] Unhandled Agent Error: {e}")
                return None

if __name__ == "__main__":
    # Isolated test run
    test_rule = "The primary action button located in the left sidebar must explicitly be labeled '+ New Waiver Request'."
    test_query = "UI Element button Location hierarchy aside text New Waiver Request"
    test_image = os.path.join(BASE_DIR, 'data/screenshots/dashboard_full.png')
    
    run_compliance_check(test_rule, test_query, test_image)