import os
import json
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("[-] GEMINI_API_KEY environment variable not found. Get a free one from Google AI Studio.")

# The new SDK uses a Client instantiation model
client = genai.Client(api_key=api_key)

DOM_FILE_PATH = os.path.join(os.path.dirname(__file__), '../data/raw_dom.json')

def analyze_dashboard():
    print("[*] Loading extracted DOM payload...")
    try:
        with open(DOM_FILE_PATH, 'r', encoding='utf-8') as f:
            dom_data = json.load(f)
    except FileNotFoundError:
        print(f"[-] Could not find {DOM_FILE_PATH}. Make sure your path is correct.")
        return

    print("[*] Dispatching payload to Gemini 3.1 Flash Lite via modern SDK...")
    
    system_prompt = """
    You are an expert QA automation agent. Your job is to compare the provided JSON representation of a web UI against strict canonical design rules.
    
    CANONICAL RULES:
    1. At the top of the sidebar, the brand "WaiverPro" must appear, followed immediately by the primary action button exactly labeled: "+ New Waiver Request".
    2. The global search input field in the header must have the exact placeholder text: "Search".
    
    YOUR TASK:
    Analyze the provided JSON DOM. Identify any discrepancies between the UI and the Canonical Rules. 
    Be brutal, specific, and output your findings in a clear list. If a rule is violated, state exactly what was found in the JSON instead.
    """

    # The new generate_content syntax
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=f"{system_prompt}\n\nUI DOM JSON:\n{json.dumps(dom_data, indent=2)}"
    )

    print("\n" + "="*30)
    print(" AI EVALUATION REPORT ")
    print("="*30)
    print(response.text)
    print("="*30 + "\n")

if __name__ == "__main__":
    analyze_dashboard()