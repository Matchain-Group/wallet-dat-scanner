#!/usr/bin/env python3
"""
scan_wallets.py

Original CLI wallet.dat scanner — backward-compatible command-line interface.

Usage:
    python3 scan_wallets.py /path/to/wallets --out report.csv --delay 0.5

Flags:
    --out FILE        Output CSV file path (default: report.csv)
    --keep-dumps      Preserve extracted wallet dump files
    --delay SECONDS   Seconds between API calls (default: 0.3)
"""

import argparse
import csv
import getpass
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("Missing dependency. Run:  pip install -r requirements.txt")
    sys.exit(1)

LINE_ADDR_RE = re.compile(r"addr=([a-km-zA-HJ-NP-Z1-9]{25,90})")
API_BASE = "https://blockstream.info/api"
RPC_PORT = 18754


class Node:
    """Manages a throwaway local bitcoind instance (no blockchain sync needed)."""

    def __init__(self):
        self.datadir = tempfile.mkdtemp(prefix="wallet_scanner_")
        self.rpcpass = f"scanner_{int(time.time())}_{os.getpid()}"
        conf_path = os.path.join(self.datadir, "bitcoin.conf")
        with open(conf_path, "w") as f:
            f.write(
                "server=1\nlisten=0\nconnect=0\ndnsseed=0\nupnp=0\n"
                f"rpcport={RPC_PORT}\nrpcuser=scanner\nrpcpassword={self.rpcpass}\n"
                "prune=550\n"
            )

    def cli(self, *args, check=True):
        cmd = ["bitcoin-cli", f"-datadir={self.datadir}",
               "-rpcuser=scanner", f"-rpcpassword={self.rpcpass}", *args]
        return subprocess.run(cmd, capture_output=True, text=True)

    def start(self):
        subprocess.run(["bitcoind", f"-datadir={self.datadir}", "-daemon"],
                        capture_output=True, text=True)
        for _ in range(30):
            r = self.cli("getblockchaininfo")
            if r.returncode == 0:
                return
            time.sleep(1)
        print("ERROR: bitcoind did not start in time.")
        sys.exit(1)

    def stop(self):
        self.cli("stop")
        time.sleep(2)

    def cleanup(self):
        shutil.rmtree(self.datadir, ignore_errors=True)


def dump_wallet(node, wallet_path, dump_dir):
    """Extract addresses from a wallet.dat file."""
    name = os.path.splitext(os.path.basename(wallet_path))[0]
    wdir = os.path.join(node.datadir, "wallets", name)
    os.makedirs(wdir, exist_ok=True)
    shutil.copy(wallet_path, os.path.join(wdir, "wallet.dat"))

    r = node.cli("loadwallet", name)
    if r.returncode != 0:
        return None

    dump_file = os.path.join(dump_dir, f"{name}_dump.txt")
    r = node.cli(f"-rpcwallet={name}", "dumpwallet", dump_file)
    if r.returncode != 0:
        passphrase = getpass.getpass(f"  Enter passphrase for '{name}' (blank to skip): ")
        if passphrase:
            node.cli(f"-rpcwallet={name}", "walletpassphrase", passphrase, "120")
            r = node.cli(f"-rpcwallet={name}", "dumpwallet", dump_file)
        if r.returncode != 0:
            node.cli("unloadwallet", name)
            return None

    node.cli("unloadwallet", name)
    return dump_file


def extract_addresses(dump_path):
    """Extract Bitcoin addresses from wallet dump file."""
    addrs = set()
    with open(dump_path, "r", errors="ignore") as f:
        for line in f:
            m = LINE_ADDR_RE.search(line)
            if m:
                addrs.add(m.group(1))
    return addrs


def get_balance_btc(address, retries=3, delay=0.3):
    """Fetch real on-chain balance from Blockstream API."""
    url = f"{API_BASE}/address/{address}"
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=15)
        except requests.RequestException:
            time.sleep(delay * (attempt + 1))
            continue
        if r.status_code == 200:
            d = r.json()
            funded = d["chain_stats"]["funded_txo_sum"] + d["mempool_stats"]["funded_txo_sum"]
            spent = d["chain_stats"]["spent_txo_sum"] + d["mempool_stats"]["spent_txo_sum"]
            return (funded - spent) / 1e8
        elif r.status_code == 429:
            time.sleep(delay * (attempt + 1))
        else:
            return None
    return None


def main():
    parser = argparse.ArgumentParser(description="Scan wallet.dat files for Bitcoin balances.")
    parser.add_argument("wallets_dir", help="Directory containing wallet.dat files")
    parser.add_argument("--out", default="report.csv", help="Output CSV file path")
    parser.add_argument("--keep-dumps", action="store_true", help="Keep extracted key dumps")
    parser.add_argument("--delay", type=float, default=0.3, help="API call delay in seconds")
    args = parser.parse_args()

    wallet_files = sorted(glob.glob(os.path.join(args.wallets_dir, "*.dat")))
    if not wallet_files:
        print(f"No .dat files found in {args.wallets_dir}")
        sys.exit(1)

    print(f"Found {len(wallet_files)} wallet.dat file(s).")
    print("Starting local, throwaway Bitcoin Core instance...")

    node = Node()
    dump_dir = tempfile.mkdtemp(prefix="wallet_dumps_")
    node.start()

    rows = []
    try:
        for i, wf in enumerate(wallet_files, 1):
            name = os.path.splitext(os.path.basename(wf))[0]
            print(f"\n== {name} ==")
            dump_file = dump_wallet(node, wf, dump_dir)
            if not dump_file:
                print("  FAILED to load wallet")
                rows.append([name, 0, 0, 0, 0.0, "FAILED"])
                continue

            addrs = extract_addresses(dump_file)
            total_btc, funded, checked = 0.0, 0, 0

            for a in addrs:
                bal = get_balance_btc(a, delay=args.delay)
                if bal is None:
                    continue
                checked += 1
                if bal > 0:
                    funded += 1
                    total_btc += bal

            status = "HAS BALANCE" if total_btc > 0 else "EMPTY"
            print(f"  OK")
            print(f"  -> {total_btc:.8f} BTC across {funded} funded address(es): {status}")
            rows.append([name, len(addrs), checked, funded, total_btc, status])

    finally:
        node.stop()
        node.cleanup()
        if not args.keep_dumps:
            shutil.rmtree(dump_dir, ignore_errors=True)

    # Write CSV
    with open(args.out, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["wallet", "addresses_found", "addresses_checked", "funded_addresses", "total_btc", "status"])
        writer.writerows(rows)

    print(f"\nReport written to: {args.out}")


if __name__ == "__main__":
    main()
