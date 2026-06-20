import os
import json
import time
from compliance_agent import run_compliance_check

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(BASE_DIR, 'data/extracted_rules.json')
REPORT_PATH = os.path.join(BASE_DIR, 'data/final_compliance_report.md')

def determine_page_context(rule_text, element):
    """
    A targeted router to map the 19 canonical rules to the 8 extracted UI states.
    """
    combined = (rule_text + " " + element).lower()
    
    # Check for specific deep-links and modals first
    if "new waiver application" in combined:
        return "new_application_modal"
    elif "facilities" in combined:
        return "facilities"
    elif "action items" in combined:
        return "action_items"
    elif "user management" in combined:
        return "user_management"
    elif "ticket" in combined:
        return "support_tickets"
    elif "settings" in combined or "faq assistant" in combined or "security" in combined:
        return "settings"
    elif "profile" in combined:
        return "profile"
    
    # Check for authentication pages
    elif "landing page" in combined or "sign in button" in combined:
        return "landing_page"
    elif "password field" in combined and "security" not in combined:
        return "login_page"
        
    # Default fallback for core application features (sidebar, header, search, tables)
    else:
        return "dashboard"

def generate_markdown_report(results):
    print(f"\n[*] Generating final Markdown report at {REPORT_PATH}...")
    
    md_content = "# WaiverPro AI Compliance Audit Report\n\n"
    md_content += "## Executive Summary\n"
    
    total = len(results)
    passed = sum(1 for r in results if r['is_compliant'])
    failed = total - passed
    
    md_content += f"- **Total Rules Evaluated:** {total}\n"
    md_content += f"- **Compliant:** {passed}\n"
    md_content += f"- **Violations Detected:** {failed}\n\n"
    md_content += "---\n\n## Detailed Findings\n\n"
    
    for res in results:
        status_icon = "✅ PASS" if res['is_compliant'] else "❌ FAIL"
        md_content += f"### {status_icon} | Rule: {res['rule']}\n"
        md_content += f"**Reasoning:** {res['reasoning']}\n\n"
        
        if not res['is_compliant'] and res.get('evidence_path'):
            rel_path = os.path.relpath(res['evidence_path'], BASE_DIR)
            # Ensure forwards slashes for markdown image links
            rel_path = rel_path.replace("\\", "/")
            md_content += f"**Visual Evidence:**\n![Violation Image](../{rel_path})\n\n"
            
        md_content += "---\n\n"
        
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print("[+] Report generation complete.")

def execute_pipeline():
    print("[*] Initializing WaiverPro Compliance Orchestrator...")
    
    try:
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            rules = json.load(f)
    except FileNotFoundError:
        print(f"[-] Could not find rulebook at {RULES_PATH}. Run extract_rules.py first.")
        return
        
    print(f"[*] Loaded {len(rules)} canonical rules. Commencing multi-page audit...")
    
    audit_results = []
    
    for index, rule_data in enumerate(rules):
        element_name = rule_data.get('element', 'Unknown Element')
        rule_desc = rule_data.get('rule', '')
        
        # 1. Route the rule to the correct UI state
        target_page = determine_page_context(rule_desc, element_name)
        screenshot_path = os.path.join(BASE_DIR, f'data/screenshots/{target_page}_full.png')
        
        full_rule_text = f"The {element_name} must satisfy this condition: {rule_desc}"
        
        # 2. Inject the [PAGE: X] tag to filter the vector database search!
        search_query = f"[PAGE: {target_page}] UI Element {element_name} {rule_desc}"
        
        print(f"\n==================================================")
        print(f"[*] Evaluating Rule {index + 1}/{len(rules)}: {element_name} (Target: {target_page})")
        
        result = run_compliance_check(full_rule_text, search_query, screenshot_path)
        
        if result:
            audit_results.append(result)
            
        time.sleep(15) 
        
    generate_markdown_report(audit_results)

if __name__ == "__main__":
    execute_pipeline()