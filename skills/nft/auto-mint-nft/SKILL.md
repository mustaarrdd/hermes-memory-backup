---
name: auto-mint-nft
title: "Auto Mint NFT from OpenSea"
description: "Auto-mint NFTs from any OpenSea collection link using the user's EVM wallet"
domain: nft, opensea, mint, ethereum
---

# Auto Mint NFT from OpenSea

Automatically detect, prepare, and submit NFT mint transactions from OpenSea collection links.

## Usage

### Mode 1 — Auto (quick, PK in script config)
1. Edit `scripts/mint.py` → set `PRIVATE_KEY` and `WALLET_ADDRESS`
2. Run: `python3 ~/.hermes/skills/nft/auto-mint-nft/scripts/mint.py <slug> [mint_price_eth]`
3. Example: `python3 ~/.hermes/skills/nft/auto-mint-nft/scripts/mint.py hellz 0`
4. Transaksi auto-kirim tanpa perlu konfirmasi manual
5. Script nampilin TX hash + link Etherscan

### Mode 2 — Prompt (safer, PK not stored)
```bash
# Set PK via env var instead (omit PRIVATE_KEY from the script config)
export MINT_PK="0x..."
python3 ~/.hermes/skills/nft/auto-mint-nft/scripts/mint.py hellz 0
```

## Example Session

```bash
$ python3 ~/.hermes/skills/nft/auto-mint-nft/scripts/mint.py hellz 0
Wallet: 0xeD0f...B86C3
Mencari koleksi 'hellz'...
Contract: 0xfb008bdd1929f93017dbc8ea2ec4057accb5f0a2
Mint function: mint() (0x2b2e2c2f)
ETH balance: 0.002002 ETH
Gas price: 2.34 Gwei
Gas estimate: 85000
Auto-kirim dalam 3 detik...

✅ Mint berhasil dikirim!
TX Hash: 0x...
Cek: https://etherscan.io/tx/0x...
```

## Key Steps

### 1. Extract Contract from OpenSea Slug

```python
import requests

def get_collection_contract(slug: str) -> str:
    """Fetch contract address from OpenSea API."""
    url = f"https://api.opensea.io/api/v2/collections/{slug}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    data = resp.json()
    return data.get('address') or data.get('primary_asset_contracts', [{}])[0].get('address')
```

### 2. Detect Mint Function

```python
# Common mint function selectors to try
MINT_SELECTORS = {
    '0x1249c58b': 'mint(uint256)',
    '0x84bb1e10': 'mint(uint256,address)',
    '0x2b2e2c2f': 'mint()',
    '0xa0712d68': 'mint(uint256)',
    '0x449a52f8': 'safeMint()',
    '0x731133e9': 'publicMint(uint256)',
    '0xe6d37b88': 'publicMint()',
    '0x66bfdcbf': 'whitelistMint(uint256,bytes32[])',
}

def detect_mint_function(contract_addr, w3):
    """Try common mint selectors on the contract."""
    code = w3.eth.get_code(w3.to_checksum_address(contract_addr))
    if len(code) < 100:
        impl = extract_proxy_impl(code)
        code = w3.eth.get_code(impl)
    code_hex = code.hex()[2:]
    for sig, name in MINT_SELECTORS.items():
        if sig[2:] in code_hex:
            return sig, name
    return None, None
```

### 3. Estimate Gas & Mint

```python
def estimate_and_mint(contract_addr, w3, account, pk, mint_price_eth=0):
    """Estimate gas and submit mint transaction."""
    contract = w3.eth.contract(
        address=w3.to_checksum_address(contract_addr),
        abi=[{'inputs': [], 'name': 'mint', 'outputs': [],
              'stateMutability': 'payable', 'type': 'function'}]
    )
    gas_estimate = contract.functions.mint().estimate_gas({
        'from': account.address,
        'value': 0
    })
    tx = contract.functions.mint().build_transaction({
        'from': account.address,
        'value': w3.to_wei(mint_price_eth, 'ether'),
        'gas': int(gas_estimate * 1.2),
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
    })
    signed = w3.eth.account.sign_transaction(tx, pk)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return w3.to_hex(tx_hash)
```

## Pitfalls

- Many mints have **merkle proofs** for allowlists — need off-chain GTD list access
- **Gas wars** — set maxFeePerGas higher than base fee
- **Mint limits** — check per-wallet max mint (some cap at 1-5)
- **Cost** — include mint price (0 ETH for free mint)
- OpenSea API rate limits — use exponential backoff
- Proxy contracts need implementation address resolved first
- Always verify mint function signature before submitting real ETH
- Some mints require exact ETH value matching mint price
- Private key must be provided fresh each time — **never hardcode in skill file**

## Example

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://ethereum-rpc.publicnode.com'))
pk = input('Paste private key: ')
account = w3.eth.account.from_key(pk)
contract_addr = get_collection_contract('hellz')
sig, name = detect_mint_function(contract_addr, w3)
if sig:
    tx_hash = estimate_and_mint(contract_addr, w3, account, pk)
    print(f'Mint submitted! TX: {tx_hash}')
else:
    print('No public mint function detected')
```
