import os
import json
from playwright.sync_api import sync_playwright

# Teleporting directly to the My Applications dashboard
TARGET_URL = "https://white-cliff-0bca3ed00.1.azurestaticapps.net/dashboard/my-applications"
AUTH_FILE_PATH = os.path.join(os.path.dirname(__file__), '../data/auth.json')
OUTPUT_DOM_PATH = os.path.join(os.path.dirname(__file__), '../data/raw_dom.json')
OUTPUT_SHOT_PATH = os.path.join(os.path.dirname(__file__), '../data/screenshots/my_applications.png')

# This JS payload traverses the live DOM, ignoring invisible elements, scripts, and svgs.
# It explicitly captures the attributes Novulis will use as traps (disabled, readonly).
CLEAN_DOM_SCRIPT = """
() => {
    function cleanNode(node) {
        if (node.nodeType === Node.ELEMENT_NODE) {
            const tag = node.tagName.toLowerCase();
            // Nuke the noise
            if (['script', 'style', 'svg', 'path', 'noscript'].includes(tag)) return null;
            
            const style = window.getComputedStyle(node);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return null;
            
            let obj = { tag: tag };
            
            // Capture critical compliance attributes
            if (node.id) obj.id = node.id;
            ['disabled', 'readonly', 'placeholder', 'type', 'href', 'value', 'name'].forEach(attr => {
                if (node.hasAttribute(attr)) obj[attr] = node.getAttribute(attr) || true;
            });

            // Extract text strictly belonging to this node
            let text = Array.from(node.childNodes)
                .filter(n => n.nodeType === Node.TEXT_NODE)
                .map(n => n.textContent.trim())
                .join(' ');
            if (text) obj.text = text;

            // Recurse through children
            let children = [];
            for (let child of node.childNodes) {
                let cleaned = cleanNode(child);
                if (cleaned) children.push(cleaned);
            }
            if (children.length > 0) obj.children = children;
            
            // Only return the node if it has actionable content or children
            return Object.keys(obj).length > 1 ? obj : null;
        } else if (node.nodeType === Node.TEXT_NODE) {
            let text = node.textContent.trim();
            return text ? { text: text } : null;
        }
        return null;
    }
    return cleanNode(document.body);
}
"""

def scrape_dashboard():
    print("[*] Launching Playwright with injected session token...")
    
    with sync_playwright() as p:
        # Running entirely in the background now
        browser = p.chromium.launch(headless=True) 
        
        # Load the golden key
        context = browser.new_context(storage_state=AUTH_FILE_PATH)
        page = context.new_page()
        
        try:
            print(f"[*] Teleporting to {TARGET_URL}...")
            page.goto(TARGET_URL)
            
            print("[*] Waiting for network idle and internal API fetches...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(4000) # Extra buffer to ensure data tables populate
            
            print("[*] Capturing visual evidence...")
            os.makedirs(os.path.dirname(OUTPUT_SHOT_PATH), exist_ok=True)
            page.screenshot(path=OUTPUT_SHOT_PATH, full_page=True)
            print(f"[+] Screenshot saved to: {OUTPUT_SHOT_PATH}")
            
            print("[*] Executing DOM cleansing payload...")
            clean_dom = page.evaluate(CLEAN_DOM_SCRIPT)
            
            print("[*] Formatting and saving JSON structure...")
            os.makedirs(os.path.dirname(OUTPUT_DOM_PATH), exist_ok=True)
            with open(OUTPUT_DOM_PATH, 'w', encoding='utf-8') as f:
                json.dump(clean_dom, f, indent=2)
            print(f"[+] Clean DOM saved to: {OUTPUT_DOM_PATH}")
            
        except Exception as e:
            print(f"[-] Scrape failed: {e}")
        finally:
            print("[*] Closing browser instance.")
            browser.close()

if __name__ == "__main__":
    scrape_dashboard()