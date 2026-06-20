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
    print("[*] Launching Playwright multi-page extraction sequence...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # --- STOP 1: THE LANDING PAGE ---
            print(f"[*] Navigating to {TARGET_URL}")
            page.goto(TARGET_URL)
            page.wait_for_load_state("networkidle") # Wait for all images/assets to download
            page.wait_for_timeout(1000) # Brief 1s buffer for final CSS animations to settle
            extract_page_data(page, "landing_page")
            
            # --- STOP 2: THE LOGIN SCREEN ---
            print("[*] Locating the entry point...")
            entry_locator = page.locator("text=/Getting Started|Get Started|Sign In/i").first
            entry_locator.wait_for(state="visible", timeout=5000)
            entry_locator.click()
            
            print("[*] Waiting for the login screen to render...")
            page.wait_for_load_state("networkidle") # Ensure login page assets are loaded
            page.wait_for_timeout(1000)
            extract_page_data(page, "login_page")

            # --- THE AUTHENTICATION INJECTION ---
            print("[*] Injecting credentials...")
            email_field = page.get_by_label("Email")
            email_field.wait_for(state="visible", timeout=5000)
            email_field.fill(USER_EMAIL)
            page.get_by_label("Password").fill(USER_PASS)
            
            print("[*] Submitting login form...")
            page.get_by_role("button", name="Login").click()
            
            # --- STOP 3: THE DASHBOARD (MY APPLICATIONS) ---
            print("[*] Waiting for initial login redirect...")
            page.wait_for_url("**/dashboard**", timeout=10000) 
            
            print("[*] Forcing navigation to My Applications view...")
            page.goto("https://white-cliff-0bca3ed00.1.azurestaticapps.net/dashboard/my-applications")
            
            print("[*] Waiting for network API calls to fetch table data...")
            page.wait_for_load_state("networkidle")
            
            print("[*] Actively monitoring DOM for skeleton loaders to vanish...")
            page.wait_for_function(
                'document.querySelectorAll(".animate-pulse").length === 0', 
                timeout=45000 
            )
            
            # A final, hard buffer to guarantee React has painted the data into the DOM
            page.wait_for_timeout(3000) 
            
            print("[+] UI fully stabilized.")
            extract_page_data(page, "dashboard")

            # --- STOP 4: USER MANAGEMENT ---
            print("\n[*] Navigating to User Management view...")
            page.goto("https://white-cliff-0bca3ed00.1.azurestaticapps.net/dashboard/user-management")
            page.wait_for_load_state("networkidle")
            page.wait_for_function('document.querySelectorAll(".animate-pulse").length === 0', timeout=45000)
            page.wait_for_timeout(2000) # Buffer for React painting
            extract_page_data(page, "user_management")

            # --- STOP 5: SUPPORT TICKETS ---
            print("\n[*] Navigating to Support Tickets view...")
            page.goto("https://white-cliff-0bca3ed00.1.azurestaticapps.net/dashboard/tickets")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            extract_page_data(page, "support_tickets")

            # --- STOP 6: SETTINGS ---
            print("\n[*] Navigating to Settings view...")
            page.goto("https://white-cliff-0bca3ed00.1.azurestaticapps.net/dashboard/settings")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            extract_page_data(page, "settings")

            # --- STOP 6.5: FACILITIES ---
            print("\n[*] Navigating to Facilities view...")
            page.goto("https://white-cliff-0bca3ed00.1.azurestaticapps.net/dashboard/facilities")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            extract_page_data(page, "facilities")

            # --- STOP 6.6: ACTION ITEMS ---
            print("\n[*] Navigating to Action Items view...")
            page.goto("https://white-cliff-0bca3ed00.1.azurestaticapps.net/dashboard/action-items")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            extract_page_data(page, "action_items")

            # --- STOP 7: PROFILE OVERLAY/VIEW ---
            print("\n[*] Opening Profile Modal/Page...")
            try:
                avatar_btn = page.locator("button:has(div.rounded-full), img.rounded-full, button[aria-label*='profile' i]").first
                if avatar_btn.is_visible():
                    avatar_btn.click()
                    page.wait_for_timeout(2000) # Wait for animation
            except Exception as inner_e:
                print(f"[-] Could not click avatar for profile drop-down: {inner_e}")
            
            extract_page_data(page, "profile")
            
            # --- STOP 8: NEW APPLICATION MODAL ---
            print("\n[*] Opening New Application Panel...")
            # Force close the profile dropdown by clicking the background, or just reload the dashboard
            page.goto("https://white-cliff-0bca3ed00.1.azurestaticapps.net/dashboard/my-applications")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            # Locate and click the "+ New Application" or "+ New Waiver Request" button
            new_app_btn = page.locator("text=/\\+ New Application|\\+ New Waiver Request/i").first
            new_app_btn.wait_for(state="visible", timeout=5000)
            new_app_btn.click()
            
            # Wait for the side-panel/modal to animate and render completely
            page.wait_for_timeout(3000)
            extract_page_data(page, "new_application_modal")
            
            # Secure the session state for future single-page testing
            os.makedirs(os.path.dirname(AUTH_FILE_PATH), exist_ok=True)
            context.storage_state(path=AUTH_FILE_PATH)
            print(f"\n[+] Session saved securely to: {AUTH_FILE_PATH}")
                
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