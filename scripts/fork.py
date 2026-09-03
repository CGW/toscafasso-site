#!/usr/bin/env python3
"""Fork toscafasso.com (Squarespace 7.1) into a static build.

Keeps the platform's own markup + CSS so layout is identical by construction.
Swaps: asset URLs (images, CSS, fonts, SVG sprite), removes platform JS,
removes cart, adds a 6-line burger-menu script.

Usage: python3 fork.py --archive archive --build build
"""
import argparse, hashlib, io, json, os, re, sys
from pathlib import Path
from urllib.parse import urlparse, unquote
import requests
from bs4 import BeautifulSoup, Comment
from PIL import Image

SITE = "https://www.toscafasso.com"
KEEP = ["home", "podcast", "the-book", "blog", "blog__tag__Podcast",
        "privacy-policy", "terms-of-service"]
WIDTHS = [100, 300, 500, 750, 1000, 1500, 2500]
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"
UA_CACHE = {}

def fetch(url, binary=True):
    if url.startswith("//"): url = "https:" + url
    if url in UA_CACHE: return UA_CACHE[url]
    r = S.get(url, timeout=60); r.raise_for_status()
    UA_CACHE[url] = r.content if binary else r.text
    return UA_CACHE[url]

# ---------- images ----------
IMG_RE = re.compile(r'https?://(?:images\.squarespace-cdn\.com|static1\.squarespace\.com)/[^\s"\'()<>]+?\.(?:png|jpe?g|gif|ico|webp)(?:\?[^\s"\'()<>]*)?', re.I)
IMG_DONE = {}   # base url -> dict(width->relpath) or single path

def img_key(url):
    base = url.split("?")[0]
    p = urlparse(base).path
    parts = [x for x in p.split("/") if x]
    stem = unquote(parts[-1])
    uid = parts[-2][:8] if len(parts) > 1 else hashlib.md5(base.encode()).hexdigest()[:8]
    return base, uid, stem

def localise_image(url, build):
    """Download original once, emit WebP variants, return (base, variants dict, ext)."""
    base, uid, stem = img_key(url)
    if base in IMG_DONE: return IMG_DONE[base]
    raw = fetch(base)
    outdir = build / "images" / uid; outdir.mkdir(parents=True, exist_ok=True)
    name, ext = os.path.splitext(stem); name = re.sub(r'[^A-Za-z0-9_-]+', '-', name).strip('-') or "img"
    ext = ext.lower()
    if ext in (".gif", ".ico"):            # keep as-is (animated gif / favicon)
        p = outdir / (name + ext); p.write_bytes(raw)
        IMG_DONE[base] = {"single": f"/images/{uid}/{name}{ext}", "w": None}
        return IMG_DONE[base]
    im = Image.open(io.BytesIO(raw)); im.load()
    W = im.width
    variants = {}
    for w in WIDTHS:
        if w > W and variants: break
        tw = min(w, W)
        v = im if tw == W else im.resize((tw, round(im.height * tw / W)), Image.LANCZOS)
        p = outdir / f"{name}-{tw}w.webp"
        if not p.exists():
            v.save(p, "WEBP", quality=82, method=6)
        variants[tw] = f"/images/{uid}/{name}-{tw}w.webp"
        if tw == W: break
    IMG_DONE[base] = {"variants": variants, "w": W}
    return IMG_DONE[base]

def best(info, want=None):
    if "single" in info: return info["single"]
    ks = sorted(info["variants"])
    if want:
        for k in ks:
            if k >= want: return info["variants"][k]
    return info["variants"][ks[-1]]

def rewrite_img_url(url, build, want=None):
    m = re.search(r'format=(\d+)w', url)
    w = int(m.group(1)) if m else want
    return best(localise_image(url, build), w)

# ---------- css ----------
CSS_DONE = {}
FONT_RE = re.compile(r'https?://[^\s"\')]+?\.(?:woff2?|otf|ttf)', re.I)

def localise_css(url, build):
    if url.startswith("//"): url = "https:" + url
    if url in CSS_DONE: return CSS_DONE[url]
    css = fetch(url).decode("utf-8", "replace")
    h = hashlib.md5(url.encode()).hexdigest()[:8]
    stem = re.sub(r'[^A-Za-z0-9_-]+', '-', os.path.basename(urlparse(url).path).replace('.css', '')) or "style"
    # fonts inside css
    def f_sub(m):
        fu = m.group(0); fn = hashlib.md5(fu.encode()).hexdigest()[:8] + os.path.splitext(fu)[1].lower()
        d = build / "assets" / "fonts"; d.mkdir(parents=True, exist_ok=True)
        (d / fn).write_bytes(fetch(fu)); return f"/assets/fonts/{fn}"
    css = FONT_RE.sub(f_sub, css)
    css = IMG_RE.sub(lambda m: rewrite_img_url(m.group(0), build), css)
    d = build / "assets" / "css"; d.mkdir(parents=True, exist_ok=True)
    rel = f"/assets/css/{stem}-{h}.css"; (build / rel.lstrip("/")).write_text(css)
    CSS_DONE[url] = rel; return rel

# ---------- html ----------
BURGER_JS = """<script>
(function(){var b=document.querySelector('.header-burger-btn'),h=document.getElementById('header');if(!b||!h)return;
b.addEventListener('click',function(){var o=h.classList.toggle('header--menu-open');b.classList.toggle('burger--active',o);document.body.classList.toggle('header--menu-open',o);b.setAttribute('aria-expanded',o);});
document.querySelectorAll('.header-menu a').forEach(function(a){a.addEventListener('click',function(){h.classList.remove('header--menu-open');b.classList.remove('burger--active');document.body.classList.remove('header--menu-open');});});
})();
</script>"""

def out_path(key):
    if key == "home": return "index.html"
    return key.replace("__", "/") + "/index.html"

def fork_page(src, build, key, log):
    html = src.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    # 1. scripts: keep JSON-LD, and keep the sqspcdn "visitor.js" component runtimes
    # (imageFluid/shape/etc — these compute layout sizing for Fluid Engine blocks
    # from data-* attributes already in the markup; removing them silently breaks
    # image/shape positioning even though the grid CSS itself is static).
    keep_scripts = set()
    for s in soup.find_all("script"):
        if s.get("type") == "application/ld+json": continue
        src = s.get("src", "")
        if "sqspcdn.com" in src and ".visitor.js" in src:
            keep_scripts.add(src); s.decompose(); continue
        s.decompose()
    for n in soup.find_all(string=lambda t: isinstance(t, Comment)): n.extract()

    # 2. head links
    for l in soup.find_all("link"):
        rel = " ".join(l.get("rel", []))
        href = l.get("href", "")
        if rel == "stylesheet" and href:
            l["href"] = localise_css(href, build)
        elif rel == "preconnect" or "typekit" in href:
            l.decompose()
        elif href and IMG_RE.match(href):
            l["href"] = rewrite_img_url(href, build)
    # block-level css declared on components
    for el in soup.find_all(attrs={"data-block-css": True}):
        try:
            urls = json.loads(el["data-block-css"])
        except Exception: urls = []
        for u in urls:
            rel = localise_css(u, build)
            if not soup.head.find("link", href=rel):
                tag = soup.new_tag("link", rel="stylesheet", href=rel); soup.head.append(tag)
        del el["data-block-css"]
        if el.has_attr("data-block-scripts"):
            try:
                for u in json.loads(el["data-block-scripts"]):
                    if ".visitor.js" in u: keep_scripts.add(u)
            except Exception: pass
            del el["data-block-scripts"]

    # 3. cart + commerce chrome
    for sel in [".header-actions-action--cart", ".showOnDesktop .header-actions-action--cart",
                ".sqs-cart-dropdown-root", ".floating-cart", ".header-skip-link"]:
        for el in soup.select(sel): el.decompose()
    for el in soup.select("a[href='/cart'], a[href$='/cart']"):
        el.decompose()

    # 4. images
    for img in soup.find_all("img"):
        for a in ("src", "data-src", "data-image"):
            if img.get(a) and IMG_RE.match(img[a]):
                img[a] = rewrite_img_url(img[a], build, 1500 if a == "src" else None)
        if img.get("srcset"):
            parts = []
            for cand in img["srcset"].split(","):
                cand = cand.strip()
                if not cand: continue
                u, _, d = cand.partition(" ")
                parts.append((rewrite_img_url(u, build) if IMG_RE.match(u) else u) + (" " + d if d else ""))
            img["srcset"] = ", ".join(parts)
        if img.get("data-load") == "false": img["data-load"] = "true"
        img["loading"] = img.get("loading", "lazy")
    # inline style / other attrs with image urls
    for el in soup.find_all(style=True):
        el["style"] = IMG_RE.sub(lambda m: rewrite_img_url(m.group(0), build), el["style"])
    for m in soup.find_all("meta"):
        c = m.get("content", "")
        if c and IMG_RE.match(c): m["content"] = SITE + rewrite_img_url(c, build)
    def f_sub(m):
        fu = m.group(0); fn = hashlib.md5(fu.encode()).hexdigest()[:8] + os.path.splitext(fu)[1].lower()
        d = build / "assets" / "fonts"; d.mkdir(parents=True, exist_ok=True)
        if not (d / fn).exists(): (d / fn).write_bytes(fetch(fu))
        return f"/assets/fonts/{fn}"
    for st in soup.find_all("style"):
        if st.string:
            st.string = IMG_RE.sub(lambda m: rewrite_img_url(m.group(0), build), st.string)
            st.string = FONT_RE.sub(f_sub, st.string)
    for st in soup.find_all("script", type="application/ld+json"):
        if st.string: st.string = IMG_RE.sub(lambda m: SITE + rewrite_img_url(m.group(0), build), st.string)

    # 5. svg sprite
    for use in soup.find_all("use"):
        for a in ("xlink:href", "href"):
            if use.get(a, "").startswith("/universal/svg/"):
                sp = build / use[a].split("#")[0].lstrip("/")
                if not sp.exists():
                    sp.parent.mkdir(parents=True, exist_ok=True); sp.write_bytes(fetch(SITE + use[a].split("#")[0]))

    # 6. links: absolute -> root-relative; kill squarespace internal domain
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if h.startswith(SITE): a["href"] = h[len(SITE):] or "/"
        elif "caper-leopard-tm8d.squarespace.com" in h: a["href"] = "/"
    # data-current-styles / data-controller attrs are inert without JS; leave.

    # 7. fonts.css + overrides.css + burger js + kept component runtimes
    soup.head.append(soup.new_tag("link", rel="stylesheet", href="/assets/css/fonts.css"))
    soup.head.append(soup.new_tag("link", rel="stylesheet", href="/assets/css/overrides.css"))
    for src in sorted(keep_scripts):
        tag = soup.new_tag("script", src=src); tag["defer"] = "defer"
        soup.body.append(tag)
    if key == "podcast":
        soup.head.append(BeautifulSoup(
            "<style>.content-width--wide .content{max-width:1400px;margin-left:auto;margin-right:auto}</style>",
            "html.parser"))
    if key == "the-book":
        # Squarespace's decorative shape block (.fe-block-82e86fb6a42b76482df0) is
        # forked verbatim with desktop grid-area: 3/10/13/24 — spanning columns
        # 10-24, which is wide enough to underlap the Amazon buy-button logo block
        # (.fe-block-4082c4d285f7ec57aecc, columns 18-23) since that logo PNG has a
        # transparent background and the shape's yellow fill / red stroke show
        # through around it. Narrow the shape to columns 10-18 so it only wraps the
        # price/buttons blocks (also columns 10-18) and stops before the logo.
        soup.head.append(BeautifulSoup(
            "<style>@media (min-width:768px){.fe-block-82e86fb6a42b76482df0{grid-area:3/10/13/18 !important}}</style>",
            "html.parser"))
    soup.body.append(BeautifulSoup(BURGER_JS, "html.parser"))

    out = build / out_path(key); out.parent.mkdir(parents=True, exist_ok=True)
    txt = str(soup)
    txt = re.sub(r'https?://caper-leopard-tm8d\.squarespace\.com', '', txt)
    txt = IMG_RE.sub(lambda m: SITE + rewrite_img_url(m.group(0), build), txt)   # anything missed (JSON-LD etc.)
    out.write_text(txt, encoding="utf-8")
    log.append((key, str(out.relative_to(build)), len(txt)))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--archive", default="archive"); ap.add_argument("--build", default="build")
    a = ap.parse_args(); arch = Path(a.archive) / "html"; build = Path(a.build)
    keys = KEEP + sorted(p.stem for p in arch.glob("blog__*.html") if p.stem != "blog__tag__Podcast")
    log = []
    for k in keys:
        src = arch / f"{k}.html"
        if not src.exists(): print("MISSING", k); continue
        fork_page(src, build, k, log); print("forked", k)
    (build / "images").mkdir(exist_ok=True)
    rep = Path("reports"); rep.mkdir(exist_ok=True)
    (rep / "fork-log.json").write_text(json.dumps({"pages": log, "images": {k: v for k, v in IMG_DONE.items()}, "css": CSS_DONE}, indent=1))
    print(len(log), "pages;", len(IMG_DONE), "images;", len(CSS_DONE), "stylesheets")

if __name__ == "__main__": main()
