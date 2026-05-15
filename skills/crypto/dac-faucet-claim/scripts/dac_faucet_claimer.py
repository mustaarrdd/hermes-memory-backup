#!/usr/bin/env python3
"""
DAC Testnet Faucet Claimer 🚀
Auto-solve Cap captcha (PoW + Instrumentation) + Claim 1 tDACC

Requirements:
  pip install playwright requests
  playwright install chromium

Usage:
  python3 dac_faucet.py <wallet_address>
  
Example:
  python3 dac_faucet.py 0xeD0fD9c3B30E4eed114D65E7Dc39E93c301B86C3
"""

import json
import sys
import time
import requests
from playwright.sync_api import sync_playwright

FAUCET_URL = "https://faucet.dachain.tech"
DISPENSE_URL = "https://faucet.dachain.tech/backend/dispense.php"
CAP_API = "https://cap.dachain.tech/81249457f9"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def solve_captcha(page, timeout=120):
    """
    Solve Cap captcha by injecting cap-widget directly into the page.
    The widget runs in a real browser, handles both PoW and instrumentation.
    Returns the captcha token string.
    """
    # Create cap-widget with correct API endpoint
    token = None
    error = None
    
    # We'll use a promise-based approach to wait for the solve
    cap_api = CAP_API
    solve_js = f"""
    (async () => {{
        try {{
            // Create cap-widget element
            const cw = document.createElement('cap-widget');
            cw.setAttribute('data-cap-api-endpoint', '{cap_api}');
            cw.style.display = 'none';
            document.body.appendChild(cw);
            
            // Solve captcha
            await cw.solve();
            const token = cw.tokenValue;
            
            // Cleanup
            cw.remove();
            
            return JSON.stringify({{ success: true, token: token }});
        }} catch (e) {{
            return JSON.stringify({{ success: false, error: e.message }});
        }}
    }})()
    """
    
    result_json = page.evaluate(solve_js)
    result = json.loads(result_json)
    
    if result.get("success"):
        return result["token"]
    else:
        raise Exception(f"Captcha solve failed: {result.get('error')}")


def claim_faucet(wallet_address, cap_token):
    """
    Call the dispense API with wallet address and captcha token.
    Returns the response message.
    """
    headers = {
        "Content-Type": "application/json",
        "Origin": FAUCET_URL,
        "Referer": f"{FAUCET_URL}/",
        "User-Agent": USER_AGENT,
    }
    
    payload = {
        "address": wallet_address,
        "cap-response": cap_token,
    }
    
    resp = requests.post(DISPENSE_URL, json=payload, headers=headers, timeout=30)
    data = resp.json()
    
    if resp.status_code == 200:
        return data.get("message", "Unknown response")
    else:
        raise Exception(f"API error ({resp.status_code}): {data.get('message', resp.text)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 dac_faucet.py <wallet_address>")
        print("Example: python3 dac_faucet.py 0xeD0fD9c3B30E4eed114D65E7Dc39E93c301B86C3")
        sys.exit(1)
    
    wallet = sys.argv[1].strip()
    
    print(f"""
╔══════════════════════════════════════╗
║    DAC Testnet Faucet Claimer v1.0   ║
╠══════════════════════════════════════╣
║  Wallet: {wallet[:38]}║
╚══════════════════════════════════════╝
    """)
    
    print("[*] Launching browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()
        
        try:
            print("[*] Opening faucet page...")
            page.goto(FAUCET_URL, wait_until="networkidle", timeout=30000)
            
            # The page imports cap-widget from CDN as an ES module.
            # We need to wait for it to be registered as a custom element.
            print("[*] Waiting for Cap widget module to load...")
            page.wait_for_function(
                "() => customElements.get('cap-widget') !== undefined",
                timeout=15000
            )
            
            print("[*] Solving Cap captcha (PoW 80 challenges)...")
            print("    This may take 20-60 seconds depending on CPU...")
            
            start = time.time()
            cap_token = solve_captcha(page)
            elapsed = time.time() - start
            
            print(f"    ✓ Captcha solved in {elapsed:.1f}s!")
            print(f"    ✓ Token: {cap_token[:50]}...")
            
            print("[*] Claiming 1 tDACC from faucet...")
            message = claim_faucet(wallet, cap_token)
            
            print(f"""
╔══════════════════════════════════════╗
║           🎉 SUCCESS! 🎉             ║
╠══════════════════════════════════════╣
║  {message[:50]}...
║                                      ║
║  Wallet: {wallet[:38]}║
╚══════════════════════════════════════╝
            """)
            
        except Exception as e:
            print(f"\n[!] Error: {e}")
            sys.exit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
