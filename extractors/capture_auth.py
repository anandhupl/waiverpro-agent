import os
import json
from playwright.sync_api import sync_playwright

TARGET_URL = "https://white-cliff-0bca3ed00.1.azurestaticapps.net/"
USER_EMAIL = "admin@gmail.com"
USER_PASS = "password"
AUTH_FILE_PATH = os.path.join(os.path.dirname(__file__), '../data/auth.json')

def extract_page_data(page, page_name="dashboard"):
    print(f"\n[*] Capturing visual evidence for {page_name}...")
    
    # 1. Ensure output directories exist so the script doesn't crash
    os.makedirs('data/screenshots', exist_ok=True)
    os.makedirs('data/dom', exist_ok=True)
    
    # 2. Take the full-page screenshot
    screenshot_path = f"data/screenshots/{page_name}_full.png"
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"[+] Screenshot secured: {screenshot_path}")

    print("[*] Extracting DOM structure with spatial bounding boxes...")
    
    # 3. Inject JS to parse the DOM and grab getBoundingClientRect()
    dom_data = page.evaluate('''() => {
        function serializeElement(el) {
            // Ignore raw text nodes at this level, we only want elements
            if (el.nodeType !== Node.ELEMENT_NODE) return null;
            
            // Skip hidden elements, scripts, and styles
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' || el.tagName === 'SCRIPT' || el.tagName === 'STYLE') {
                return null;
            }

            // Grab the exact spatial coordinates of the element
            const rect = el.getBoundingClientRect();
            
            // Trap: Only capture elements that actually take up visible space on the screen
            if (rect.width === 0 || rect.height === 0) return null;

            const nodeData = {
                tag: el.tagName.toLowerCase(),
                text: Array.from(el.childNodes)
                    .filter(n => n.nodeType === Node.TEXT_NODE)
                    .map(n => n.textContent.trim())
                    .join(' ')
                    .replace(/\\s+/g, ' ')
                    .trim(),
                attributes: {},
                boundingBox: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                children: []
            };

            // Filter out noise: only keep attributes useful for AI reasoning
            for (const attr of el.attributes) {
                if (['id', 'class', 'href', 'placeholder', 'type', 'name', 'src'].includes(attr.name)) {
                    nodeData.attributes[attr.name] = attr.value;
                }
            }

            // Recursively process children
            for (const child of el.children) {
                const childData = serializeElement(child);
                if (childData) {
                    nodeData.children.push(childData);
                }
            }
            
            return nodeData;
        }
        
        return serializeElement(document.body);
    }''')
    
    # 4. Save the enriched DOM
    dom_path = f"data/dom/{page_name}_raw.json"
    with open(dom_path, 'w', encoding='utf-8') as f:
        json.dump(dom_data, f, indent=2)
        
    print(f"[+] Enriched DOM payload secured: {dom_path}")
    return dom_data


def capture_session():
    print("[*] Launching Playwright to capture authentication state...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print(f"[*] Navigating to {TARGET_URL}")
            page.goto(TARGET_URL)
            
            print("[*] Waiting for the page to physically load...")
            page.wait_for_timeout(5000)
            
            print("[*] Locating the entry point...")
            entry_locator = page.locator("text=/Getting Started|Get Started|Sign In/i").first
            
            entry_locator.wait_for(state="visible", timeout=5000)
            print("[*] Found entry point. Clicking...")
            entry_locator.click()
            
            print("[*] Waiting for the login screen to render...")
            page.wait_for_timeout(3000)

            print("[*] Injecting credentials...")
            email_field = page.get_by_label("Email")
            email_field.wait_for(state="visible", timeout=5000)
            email_field.fill(USER_EMAIL)
            page.get_by_label("Password").fill(USER_PASS)
            
            print("[*] Submitting login form...")
            page.get_by_role("button", name="Login").click()
            
            print("[*] Waiting for dashboard redirect...")
            page.wait_for_url("**/dashboard**", timeout=10000) 
            
            # THE RACE CONDITION FIX:
            print("[*] Allowing DOM to mount initial skeleton state...")
            page.wait_for_timeout(2000) # Give the frontend 2 seconds to paint the skeletons
            
            print("[*] Actively monitoring DOM for skeleton loaders to vanish...")
            page.wait_for_function(
                'document.querySelectorAll(".animate-pulse").length === 0', 
                timeout=45000 
            )
            
            # Tiny buffer for the final text nodes to populate
            page.wait_for_timeout(1500) 
            
            print("[+] UI fully stabilized. Extracting browser state.")
            os.makedirs(os.path.dirname(AUTH_FILE_PATH), exist_ok=True)
            context.storage_state(path=AUTH_FILE_PATH)
            
            print("[+] Authentication successful. Extracting browser state.")
            os.makedirs(os.path.dirname(AUTH_FILE_PATH), exist_ok=True)
            context.storage_state(path=AUTH_FILE_PATH)
            print(f"[+] Session saved securely to: {AUTH_FILE_PATH}")
            
            # THE FIX: Trigger the data and visual extraction immediately after auth
            extract_page_data(page, "dashboard")
                
        except Exception as e:
            print(f"\n[-] Extraction failed: {e}")
            os.makedirs(os.path.dirname(AUTH_FILE_PATH), exist_ok=True)
            err_shot = os.path.join(os.path.dirname(__file__), '../data/error_state.png')
            page.screenshot(path=err_shot)
            print(f"[*] Error screenshot saved to: {err_shot}\n")
        finally:
            print("[*] Closing browser instance.")
            browser.close()

if __name__ == "__main__":
    capture_session()