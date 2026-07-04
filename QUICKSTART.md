# Quick Start Guide — 5 Minutes to Your First Scan

## Installation (2 min)

```bash
# 1. Clone or download this repository
git clone <repo-url>
cd wallet-dat-scanner

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify Bitcoin Core is installed
bitcoind -version
bitcoin-cli -version
```

If Bitcoin Core is missing, download from: **https://bitcoincore.org/en/download/**  
(Version 22.x–25.x recommended)

---

## Run the Dashboard (1 min)

```bash
python wallet_dashboard.py
```

You'll see:

```
======================================================================
              BITCOIN WALLET SCANNER DASHBOARD
              Secure • Fast • Transparent • Open Source
======================================================================

What would you like to do?

[1] Scan wallet.dat files from directory
[2] Extract and scan wallet.dat from ZIP archive
[3] Paste private keys directly
[4] View previous reports
[5] Configure settings
[0] Exit

Enter your choice (0-5):
```

---

## Example Workflow

### Scenario 1: You have wallet.dat files in a folder

```
1. Press [1]
2. Enter path: /path/to/my/wallets
3. Tool lists found files
4. Confirm with [y]
5. Grab a coffee ☕ (scan takes ~5-45 min depending on wallet count)
6. Check results on screen
7. Find reports in ./wallet_reports/
```

### Scenario 2: You have a ZIP file with wallets

```
1. Press [2]
2. Enter ZIP path: /path/to/wallets.zip
3. Tool extracts and scans
4. Reports saved to ./wallet_reports/
```

### Scenario 3: You want to check a private key

```
1. Press [3]
2. Paste your WIF format private key (starts with 5, K, or L)
3. Press Ctrl+D (Mac/Linux) or Ctrl+Z + Enter (Windows)
4. Tool checks on-chain balance
5. View result immediately
```

---

## Understanding the Output

After a scan, you'll see:

```
======================================================================
                          RESULTS SUMMARY
======================================================================

Total BTC found: 0.45210000
Wallets with balance: 2/5

Wallet               Addresses    Funded     Balance (BTC)   Status
------------------------------------------------------------------------
wallet_07            40           3          0.45210000      HAS BALANCE
wallet_33            8            1          0.00120000      HAS BALANCE
wallet_01            12           0          0.00000000      EMPTY

✓ CSV report: ./wallet_reports/scan_20260704_120530.csv
✓ JSON report: ./wallet_reports/scan_20260704_120530.json
```

**Key columns:**
- **Wallet** = filename of the .dat file
- **Addresses** = number of addresses extracted from this wallet
- **Funded** = how many addresses have ANY Bitcoin on them
- **Balance (BTC)** = total BTC in this wallet
- **Status** = "HAS BALANCE" (you might have funds!) or "EMPTY"

---

## What Happens Next?

### If you found funds:

1. **BACKUP everything first** (just in case)
2. Create a brand-new, empty Bitcoin wallet (with a new, strong seed phrase)
3. Use `bitcoin-cli sweepaddress` or the GUI to move all funds to the new wallet
4. Once confirmed on-chain, your funds are safe in the new, secure wallet
5. Never reuse the old wallet.dat again

### If all wallets are empty:

✓ You can archive or delete the old wallet files safely

---

## Customizing Settings

Press [5] to adjust:

- **API Delay** — Default 0.3s. Increase if you hit rate limits (try 1.0s)
- **Keep Dumps** — Default OFF. Don't enable unless you need the private key dumps
- **Output Directory** — Where reports are saved

---

## Troubleshooting

**"bitcoind not found"**
→ Install Bitcoin Core: https://bitcoincore.org/en/download/

**"Failed to load wallet"**
→ Your .dat file might be from old Bitcoin (pre-0.8). Try installing Bitcoin Core 23.x.

**"Rate limit 429 error"**
→ Blockstream API is limiting you. Increase API delay to 1.0–2.0 seconds in Settings [5].

**"Permission denied on .dat file"**
→ Run: `chmod 644 /path/to/wallet.dat`

---

## Security Reminders

✅ Run this on a **trusted machine** (air-gapped if paranoid)  
✅ **Never upload** actual wallet.dat files online  
✅ **Don't commit** .dat files to GitHub (`.gitignore` prevents this)  
✅ **Delete** old wallets after sweeping funds  
✅ **Backup** important stuff before running anything  

---

## Need More Help?

Read the full guide: `README_DASHBOARD.md`

---

**That's it! You're ready to scan your old wallets.** 🚀
