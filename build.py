"""Build the portfolio site.

    python build.py            # renders everything into _site/
    python build.py --serve    # build, then serve _site/ on http://localhost:8000

Content lives in content/ (YAML + Markdown), layout in templates/, and files that
are copied as-is in static/. See README.md for how to edit content.
"""
from __future__ import annotations

import datetime as dt
import html
import re
import shutil
import sys
from functools import lru_cache
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

try:
    from PIL import Image
except ImportError:  # image sizes are optional; pages still build without Pillow
    Image = None

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
OUT = ROOT / "_site"

FUNCTIONS = {
    "strategy": "Strategy",
    "bd": "Business development",
    "analytics": "Analytics & finance",
    "regulatory": "Regulatory",
    "marketing": "Marketing & comms",
}


# --------------------------------------------------------------------------- content
def check_text_lists(data, where: str) -> None:
    """Catch the classic YAML trap: an unquoted line containing ': ' becomes a
    key/value pair instead of text, and would show up on the site as {'…': '…'}."""
    problems: list[str] = []

    def walk(x, path):
        if isinstance(x, list):
            if any(isinstance(i, str) for i in x):
                for v in x:
                    if isinstance(v, dict):
                        k, val = next(iter(v.items()))
                        problems.append(f'  "{k}: {val}"')
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{path}.{k}")

    walk(data, where)
    if problems:
        sys.exit(
            f"\n{where}: these lines contain a colon followed by a space, so YAML read them as\n"
            "key/value pairs instead of text. Wrap each line in double quotes to fix it:\n"
            + "\n".join(problems)
        )


def load_yaml(name: str):
    with open(CONTENT / name, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    check_text_lists(data, f"content/{name}")
    return data


MD = markdown.Markdown(extensions=["tables", "attr_list", "sane_lists", "smarty"])


def md(text: str | None) -> Markup:
    if not text:
        return Markup("")
    MD.reset()
    out = MD.convert(text)
    # open external links in a new tab, safely
    out = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', out)
    # wrap tables so they can scroll horizontally on phones
    out = out.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    return Markup(out)


def md_inline(text: str | None) -> Markup:
    """Markdown for a single line (no wrapping <p>)."""
    out = str(md(text)).strip()
    if out.startswith("<p>") and out.endswith("</p>") and out.count("<p>") == 1:
        out = out[3:-4]
    return Markup(out)


def load_projects() -> list[dict]:
    projects = []
    for path in sorted((CONTENT / "projects").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
        if not m:
            sys.exit(f"{path.name}: missing '---' front matter block")
        meta = yaml.safe_load(m.group(1)) or {}
        check_text_lists(meta, f"content/projects/{path.name}")
        for key in ("title", "summary", "context", "sector", "year", "image_alt", "disclaimer", "artifacts"):
            if key in meta and not isinstance(meta[key], str):
                sys.exit(f"content/projects/{path.name}: '{key}' must be text. Wrap the value in double quotes.")
        meta.setdefault("slug", path.stem)
        meta.setdefault("has_page", True)
        meta.setdefault("featured", False)
        meta.setdefault("order", 100)
        meta.setdefault("functions", [])
        meta.setdefault("tags", [])
        unknown = set(meta["functions"]) - FUNCTIONS.keys()
        if unknown:
            sys.exit(f"{path.name}: unknown functions {unknown}; use {list(FUNCTIONS)}")
        meta["body"] = md(m.group(2))
        meta["url"] = f"/work/{meta['slug']}/" if meta["has_page"] else meta.get("link", "/work/")
        meta["source"] = path.name
        if meta.get("draft"):
            continue
        projects.append(meta)
    projects.sort(key=lambda p: (p["order"], p["title"]))
    for i, p in enumerate(projects, 1):
        p["index"] = i
    return projects


# --------------------------------------------------------------------------- helpers
@lru_cache(maxsize=None)
def image_size(src: str) -> tuple[int, int] | None:
    if Image is None or not src.startswith("/static/"):
        return None
    path = ROOT / src.lstrip("/")
    if not path.exists():
        return None
    with Image.open(path) as im:
        return im.size


def img(src: str, alt: str, cls: str = "", loading: str = "lazy", sizes: str | None = None) -> Markup:
    size = image_size(src)
    attrs = [f'src="{html.escape(src)}"', f'alt="{html.escape(alt)}"']
    if size:
        attrs += [f'width="{size[0]}"', f'height="{size[1]}"']
    if cls:
        attrs.append(f'class="{cls}"')
    if loading:
        attrs.append(f'loading="{loading}"')
    attrs.append('decoding="async"')
    if sizes:
        attrs.append(f'sizes="{sizes}"')
    return Markup(f"<img {' '.join(attrs)}>")


# --------------------------------------------------------------------------- render
def build() -> None:
    site = load_yaml("site.yaml")
    experience = load_yaml("experience.yaml")
    creative = load_yaml("creative.yaml")
    projects = load_projects()

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT / "static")

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.tests["contains"] = lambda seq, item: item in seq
    env.filters["md"] = md
    env.filters["mdi"] = md_inline
    env.globals.update(
        site=site,
        img=img,
        functions=FUNCTIONS,
        year=dt.date.today().year,
        updated=dt.date.today().strftime("%B %Y"),
    )

    pages: list[str] = []

    def render(template: str, out: str, **ctx) -> None:
        target = OUT / out
        target.parent.mkdir(parents=True, exist_ok=True)
        path = "/" + out.removesuffix("index.html")
        target.write_text(env.get_template(template).render(page_path=path, **ctx), encoding="utf-8")
        if not out.startswith("404"):
            pages.append(path)

    featured = [p for p in projects if p["featured"]]
    render("home.html", "index.html", experience=experience, featured=featured, projects=projects)
    render("work.html", "work/index.html", projects=projects)
    for p in projects:
        if p["has_page"]:
            others = [q for q in projects if q is not p and q["has_page"]]
            # suggest projects that share a function first
            others.sort(key=lambda q: (-len(set(q["functions"]) & set(p["functions"])), q["order"]))
            render("project.html", f"work/{p['slug']}/index.html", project=p, related=others[:3])
    render("creative.html", "creative/index.html", creative=creative)
    render("404.html", "404.html")

    base = site["url"].rstrip("/")
    today = dt.date.today().isoformat()
    sitemap = "\n".join(f"  <url><loc>{base}{p}</loc><lastmod>{today}</lastmod></url>" for p in pages)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap}\n</urlset>\n',
        encoding="utf-8",
    )
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    problems = check_links()
    print(f"Built {len(pages)} pages + 404 into {OUT.relative_to(ROOT)}/")
    if problems:
        print("\nBroken internal links:")
        for p in problems:
            print("  " + p)
        sys.exit(1)


def check_links() -> list[str]:
    """Every internal href/src in the output must point at a real file (or #anchor)."""
    problems = []
    ids_by_page: dict[Path, set[str]] = {}
    for page in OUT.rglob("*.html"):
        ids_by_page[page] = set(re.findall(r'\sid="([^"]+)"', page.read_text(encoding="utf-8")))
    for page, _ in ids_by_page.items():
        text = page.read_text(encoding="utf-8")
        for url in re.findall(r'(?:href|src|data-src)="([^"]+)"', text) + re.findall(r'"(/static/[^"]+)"', text):
            if url.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            path, _, anchor = url.partition("#")
            if not path:  # same-page anchor
                target = page
            elif path.startswith("/"):
                target = OUT / path.lstrip("/")
                if path.startswith("/static/") and target.is_dir():
                    continue  # base paths such as data-base="/static/media/creative/"
                if path.endswith("/") or target.is_dir():
                    target = target / "index.html"
            else:
                continue
            if not target.exists():
                problems.append(f"{page.relative_to(OUT)} -> {url}")
            elif anchor and target.suffix == ".html" and anchor not in ids_by_page.get(target, set()):
                problems.append(f"{page.relative_to(OUT)} -> {url} (missing #{anchor})")
    return sorted(set(problems))


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import functools
        import http.server

        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Serving on http://localhost:8000  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
