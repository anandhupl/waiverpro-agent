import os
from playwright.sync_api import sync_playwright

TARGET_URL = "https://white-cliff-0bca3ed00.1.azurestaticapps.net/"
USER_EMAIL = "admin@gmail.com"
USER_PASS = "password"
AUTH_FILE_PATH = os.path.join(os.path.dirname(__file__), '../data/auth.json')

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
            # The fix: Target the actual button, not the h1 heading
            page.get_by_role("button", name="Login").click()
            
            print("[*] Waiting for dashboard redirect...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000) 
            
            print("[+] Authentication successful. Extracting browser state.")
            os.makedirs(os.path.dirname(AUTH_FILE_PATH), exist_ok=True)
            context.storage_state(path=AUTH_FILE_PATH)
            print(f"[+] Session saved securely to: {AUTH_FILE_PATH}")
                
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