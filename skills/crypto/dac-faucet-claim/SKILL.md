---
name: dac-faucet-claim
description: Claim 1 tDACC from DAC Testnet Faucet by auto-solving Cap captcha via browser
usage: |
  To claim: Run the script with your wallet address:
  ```
  python3 /root/.hermes/skills/crypto/dac-faucet-claim/scripts/dac_faucet_claimer.py <wallet_address>
  ```
  Or ask Bae: "Claim tDACC ke wallet [address]"

requirements:
  - playwright (pip install playwright, playwright install chromium)
  - requests

flow:
  1. Opens faucet.dachain.tech in Playwright headless Chromium
  2. Waits for Cap widget custom element to register
  3. Injects cap-widget element, calls solve() 
  4. Solves 80 PoW SHA-256 challenges automatically
  5. Decodes/executes instrumention fingerprint in-browser
  6. Gets captcha token
  7. Posts to /backend/dispense.php with wallet address + token
  8. Returns success message

notes:
  - Cap captcha is NOT visual - it's Proof-of-Work (80 challenges × 16 bit = ~5M hashes)
  - Instrumentation requires real browser DOM (Playwright provides this)
  - Timeout ~120s, but typically finishes in 20-60s
  - Each wallet can only claim once per 7 days according to their docs
  - Script at ~/.hermes/skills/crypto/dac-faucet-claim/scripts/dac_faucet_claimer.py
---
