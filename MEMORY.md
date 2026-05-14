When setting up Hermes Gateway, it's more reliable to run `hermes gateway setup` interactively first to configure platforms, then run `hermes gateway install` to set up the service. Attempting to fully automate the setup via pipes or scripts can be unreliable due to interactive prompts in the setup wizard.
§
Persona is "Bae" — female, gentle, soft personality. Same technical skills.
§
Custom EVM Network: PentaChain, Chain ID 7777, RPC rpc.pentamine.org, Symbol PENTA
§
Created custom 'auto-mint-nft' skill for user — auto-mints NFTs from OpenSea collection links. Script at ~/.hermes/skills/nft/auto-mint-nft/scripts/mint.py — PK via MINT_PK env var (no longer hardcoded). Usage: python3 mint.py <slug> [mint_price_eth]
§
For auto-minting NFTs from OpenSea: extract slug from URL, get contract via opensea.io API v2 (works without API key - just User-Agent header), check if contract uses SeaDrop standard (mintSeaDrop function selector 0x64869dad), use w3.eth.contract with SeaDrop ABI, check getMintStats for availability, call mintSeaDrop(wallet, quantity) with payable value. Most SeaDrop mints require ETH value matching mint price from getPublicDrop config. Script at ~/.hermes/skills/nft/auto-mint-nft/scripts/mint.py — uses MINT_PK env var (not hardcoded).
§
Bae's own EVM wallet: 0xDbD817773314D8B214B3755633de2F0573834C59 — saved in ~/.hermes/credentials.json. Private key stored only in that file, not in memory.
§
Bae's X: @MbgAgent, OAuth 1.0a via xurl (read-only, posting butuh Basic $100/mo). Gmail: mbgagent5@gmail.com, via Himalaya CLI. Creds in ~/.hermes/credentials.json. x-post.py at /root/x-post.py.
§
User has access to api.b.ai — OpenAI-compatible endpoint. Models available: gpt-5.2, deepseek-v4-flash (reasoning model). Could config as Hermes provider if needed.
§
9Router v0.4.41 — AI multi-router dashboard at localhost:20128 (pw default: 123456). Endpoint /v1 (OpenAI-compatible). Support 30+ providers, usage tracking, quota monitor. Wajib install better-sqlite3 dulu: cd /root/.9router/runtime && npm install better-sqlite3@12.6.2 (tanpa ini crash SIGKILL). Start pake --skip-update. Cloudflare tunnel auto-generated tiap restart.