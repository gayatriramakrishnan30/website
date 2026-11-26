"""Render static/img/og-image.png (the 1200x630 LinkedIn / social preview card).

Uses Microsoft Edge (or Chrome) in headless mode so the card is drawn with the
site's own fonts. Re-run after changing your name, headline or photo:

    python tools/make_og.py
"""
from __future__ import annotations

import functools
import http.server
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
]

site = yaml.safe_load((ROOT / "content" / "site.yaml").read_text(encoding="utf-8"))
roles = "<br>".join(f"{r['role']} · {r['org']}" for r in site["current_roles"])

HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Fraunces; src: url(/static/fonts/fraunces-var.woff2); font-weight: 300 900; }}
@font-face {{ font-family: Fraunces; src: url(/static/fonts/fraunces-var-italic.woff2); font-weight: 300 900; font-style: italic; }}
@font-face {{ font-family: Inter; src: url(/static/fonts/inter-var.woff2); font-weight: 100 900; }}
* {{ margin: 0; box-sizing: border-box; }}
html, body {{ width: 1200px; height: 630px; overflow: hidden; }}
body {{ background: #f6f4ef; color: #15201f; font-family: Inter, sans-serif; position: relative; }}
.grid {{ position: absolute; inset: 0; background-image: linear-gradient(#ddd8cc 1px, transparent 1px), linear-gradient(90deg, #ddd8cc 1px, transparent 1px);
  background-size: 36px 36px; opacity: .5; -webkit-mask-image: radial-gradient(ellipse 60% 70% at 80% 40%, #000 15%, transparent 70%); }}
.text {{ position: absolute; left: 72px; top: 64px; width: 640px; }}
.mark {{ display: inline-grid; place-items: center; width: 52px; height: 52px; border-radius: 50%; background: #17656d; color: #f6f4ef;
  font-family: Fraunces, serif; font-weight: 600; font-size: 21px; }}
.name {{ margin-top: 40px; font-size: 26px; font-weight: 600; color: #17656d; letter-spacing: .01em; }}
.headline {{ margin-top: 14px; font-family: Fraunces, serif; font-size: 66px; line-height: 1.04; letter-spacing: -.025em; font-weight: 450;
  font-variation-settings: "SOFT" 50, "WONK" 1; }}
.roles {{ position: absolute; left: 72px; bottom: 62px; width: 660px; font-size: 19px; color: #3a4644; line-height: 1.5; }}
.roles b {{ display: block; font-size: 14px; letter-spacing: .16em; text-transform: uppercase; color: #5e6a67; margin-bottom: 6px; font-weight: 650; }}
.photo {{ position: absolute; right: 72px; top: 70px; width: 330px; height: 430px; }}
.photo::before {{ content: ""; position: absolute; inset: 16px -16px -16px 16px; border: 2px solid #17656d; border-radius: 22px; opacity: .55; }}
.photo img {{ position: relative; width: 100%; height: 100%; object-fit: cover; object-position: 50% 30%; border-radius: 22px;
  box-shadow: 0 24px 48px -20px rgba(21,32,31,.35); }}
.bar {{ position: absolute; left: 0; right: 0; bottom: 0; height: 10px; background: #17656d; }}
</style></head><body>
<div class="grid"></div>
<div class="text">
  <span class="mark">GR</span>
  <p class="name">{site['name']}</p>
  <p class="headline">{site['headline']}</p>
</div>
<div class="roles"><b>Life sciences · {site['location']}</b>{roles}</div>
<div class="photo"><img src="/static/img/photo.jpg" alt=""></div>
<div class="bar"></div>
</body></html>"""


def main() -> None:
    browser = next((b for b in BROWSERS if Path(b).exists() or shutil.which(b)), None)
    if not browser:
        raise SystemExit("Edge or Chrome is needed to render the preview image.")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copytree(ROOT / "static", tmp / "static")
        (tmp / "og.html").write_text(HTML, encoding="utf-8")
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp))
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):  # keep the console tidy
                pass
        handler = functools.partial(Quiet, directory=str(tmp))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        out = ROOT / "static" / "img" / "og-image.png"
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--virtual-time-budget=4000", "--window-size=1200,630", f"--screenshot={out}",
                        f"http://127.0.0.1:{server.server_address[1]}/og.html"], capture_output=True, timeout=90)
        server.shutdown()
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
