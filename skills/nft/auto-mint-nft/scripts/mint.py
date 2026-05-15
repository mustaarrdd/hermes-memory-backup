#!/usr/bin/env python3
"""
Auto Mint NFT - Template Script
Usage: python3 mint.py <opensea_slug> [mint_price_eth]
Example: python3 mint.py hellz 0
"""

import sys
import json
import requests
from web3 import Web3

# ── Config ─────────────────────────────────────────────────────────────
RPC_URL = "https://ethereum-rpc.publicnode.com"

# ── Wallet ──────────────────────────────────────────────────────────────
# Mode A: Hardcode PK here for auto mode (quick but exposed in file)
# Mode B: Set env var MINT_PK instead (safer — uncomment line below to use)
import os
PRIVATE_KEY = os.environ.get("MINT_PK")
if not PRIVATE_KEY:
    print("❌ MINT_PK env var gak diset. Set dulu: export MINT_PK=0x...")
    sys.exit(1)
WALLET_ADDRESS = None  # Auto-derived from PRIVATE_KEY below

# ── Common Mint Function Selectors ─────────────────────────────────────
MINT_SELECTORS = {
    "0x1249c58b": "mint(uint256)",
    "0x84bb1e10": "mint(uint256,address)",
    "0x2b2e2c2f": "mint()",
    "0xa0712d68": "mint(uint256)",
    "0x449a52f8": "safeMint()",
    "0x731133e9": "publicMint(uint256)",
    "0xe6d37b88": "publicMint()",
    "0x66bfdcbf": "whitelistMint(uint256,bytes32[])",
    "0x64869dad": "mintSeaDrop(address,uint256)",  # OpenSea SeaDrop
    "0x44dae42c": "setRoyaltyInfo((address,uint96))",
}

# SeaDrop ABI for mintSeaDrop
SEADROP_MINT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "minter", "type": "address"},
            {"internalType": "uint256", "name": "quantity", "type": "uint256"},
        ],
        "name": "mintSeaDrop",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
]

def get_collection(slug):
    url = f"https://api.opensea.io/api/v2/collections/{slug}"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    return resp.json()

def extract_contract(data):
    addr = data.get("address")
    if addr:
        return addr
    contracts = data.get("primary_asset_contracts", [])
    if contracts:
        return contracts[0].get("address")
    chains = data.get("addresses", {})
    for chain, info in chains.items():
        if info.get("address"):
            return info["address"]
    return None

def extract_proxy_impl(code_hex):
    # EIP-1167 minimal proxy: 363d3d373d3d3d363d73 + 20 bytes impl + 5af43d82803e903d91602b57fd5bf3
    if code_hex.startswith("363d3d373d3d3d363d73"):
        impl_bytes = bytes.fromhex(code_hex[20:60])
        return Web3.to_checksum_address(impl_bytes.hex())
    return None

def detect_mint(w3, contract_addr):
    addr = Web3.to_checksum_address(contract_addr)
    code = w3.eth.get_code(addr)
    if len(code) < 100:
        impl = extract_proxy_impl(code.hex()[2:])
        if impl:
            code = w3.eth.get_code(impl)
    code_hex = code.hex()[2:]
    for sig, name in MINT_SELECTORS.items():
        if sig[2:] in code_hex:
            return sig, name
    return None, None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mint.py <opensea_slug> [mint_price_eth]")
        print("Example: python3 mint.py hellz 0")
        sys.exit(1)

    slug = sys.argv[1]
    mint_price = float(sys.argv[2]) if len(sys.argv) > 2 else 0

    # PK from config
    pk = PRIVATE_KEY

    # Connect
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("Gagal konek ke Ethereum RPC")
        sys.exit(1)

    account = w3.eth.account.from_key(pk)
    print(f"Wallet: {account.address}")

    # Get collection info
    print(f"Mencari koleksi '{slug}'...")
    data = get_collection(slug)
    contract_addr = extract_contract(data)
    if not contract_addr:
        print("Gak nemu contract address dari OpenSea API")
        sys.exit(1)
    print(f"Contract: {contract_addr}")

    # Detect mint function
    sig, name = detect_mint(w3, contract_addr)
    if not sig:
        print("Gak nemu public mint function di contract ini")
        print("Mungkin mint-nya pake allowlist / whitelist / merkle proof")
        sys.exit(1)
    print(f"Mint function: {name} ({sig})")

    # Check balance
    eth_balance = w3.eth.get_balance(account.address)
    eth_display = w3.from_wei(eth_balance, "ether")
    print(f"ETH balance: {eth_display:.6f} ETH")

    if eth_balance < w3.to_wei(mint_price + 0.0005, "ether"):
        print(f"Gas/Eth gak cukup! Butuh ~{mint_price + 0.0005} ETH, cuma punya {eth_display:.6f} ETH")
        sys.exit(1)

    # Build & Send Transaction
    gas_price = w3.eth.gas_price
    print(f"Gas price: {w3.from_wei(gas_price, 'gwei'):.2f} Gwei")

    mint_abi = [{"inputs": [], "name": "mint", "outputs": [],
                 "stateMutability": "payable", "type": "function"}]
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=mint_abi)

    try:
        gas_estimate = contract.functions.mint().estimate_gas({
            "from": account.address,
            "value": w3.to_wei(mint_price, "ether")
        })
        print(f"Gas estimate: {gas_estimate}")
    except Exception as e:
        print(f"Gas estimation gagal: {e}")
        gas_estimate = 150000  # Fallback

    tx = contract.functions.mint().build_transaction({
        "from": account.address,
        "value": w3.to_wei(mint_price, "ether"),
        "gas": int(gas_estimate * 1.5),
        "gasPrice": int(gas_price * 1.1),
        "nonce": w3.eth.get_transaction_count(account.address),
    })

    total_cost = w3.from_wei(w3.to_wei(mint_price, "ether") + tx["gas"] * tx["gasPrice"], "ether")
    print(f"Mint price: {mint_price} ETH")
    print(f"Max gas cost: ~{w3.from_wei(tx['gas'] * tx['gasPrice'], 'ether'):.6f} ETH")
    print(f"Total: ~{total_cost:.6f} ETH")
    print("Auto-kirim dalam 3 detik...")
    import time
    time.sleep(3)

    signed = w3.eth.account.sign_transaction(tx, pk)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"\n✅ Mint berhasil dikirim!")
    print(f"TX Hash: {w3.to_hex(tx_hash)}")
    print(f"Cek: https://etherscan.io/tx/{w3.to_hex(tx_hash)}")

if __name__ == "__main__":
    main()
