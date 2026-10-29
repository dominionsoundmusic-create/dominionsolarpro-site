#!/usr/bin/env python3
"""Dominion Solar Pro page builder.

Each file in _build/pages/ holds one page: a JSON header between <!--META and META-->,
then the page body HTML. This script wraps every body in the shared design
(scripture bar, Duplantis quote, header with Espanol button, full-width hero,
footer, delayed GA4) and writes it to <slug>/index.html.

Speed rules applied automatically:
  - every photo gets WebP copies at 480/800/1200/1600 wide in /images/w/
  - images are served with <picture> + srcset, JPEG kept as fallback
  - the hero is preloaded with fetchpriority="high"; other images lazy-load
  - CSS is inlined; no web fonts are loaded (system font stack)
  - GA4 loads on first interaction or 3.5s after load

Usage: python3 _build/build.py            (builds every page)
       python3 _build/build.py off-grid-solar-power
"""
import json, re, sys, html
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "_build" / "pages"
IMG = ROOT / "images"
WEBP = IMG / "w"
SITE = "https://dominionsolarpro.com"
WIDTHS = [480, 800, 1200, 1600]
GA = "G-KZXHGGW4VE"

NAV = [
    ("Off-Grid Power", "/off-grid-solar-power/"),
    ("Best Solar Generator", "/best-solar-generator/"),
    ("RV", "/solar-generator-for-rv/"),
    ("Home Backup", "/solar-generator-for-home-backup/"),
    ("Solar Panels", "/solar-panels/"),
]

CSS = """
:root{--pine:#12281F;--moss:#1D3B2C;--amber:#FFB020;--ember:#E4571B;--ink:#0E1A14;--muted:#4A5850;--line:#C9D3CC;--sky:#0B5A7A;--rail:clamp(22px,5.5vw,140px)}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:#fff;color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-size:18px;line-height:1.65;-webkit-font-smoothing:antialiased}
img{max-width:100%;display:block}a{color:var(--sky)}a:hover{color:var(--ember)}
:focus-visible{outline:3px solid var(--amber);outline-offset:2px}
.scripture{background:var(--ink);color:#fff;text-align:center;font-size:13px;font-weight:700;letter-spacing:.06em;padding:6px var(--rail)}
.creed{background:var(--amber);color:var(--ink);text-align:center;font-size:14px;padding:8px var(--rail)}
.creed b{font-weight:800}
.site-head{position:sticky;top:0;z-index:50;background:var(--pine);border-bottom:3px solid var(--amber)}
.head-in{display:flex;align-items:center;gap:22px;padding:12px var(--rail);flex-wrap:wrap}
.brand{order:0;display:flex;align-items:center;gap:10px;color:#fff;text-decoration:none;font-weight:800;font-size:19px;letter-spacing:-.01em}
.brand-mark{width:24px;height:24px;border-radius:50%;background:radial-gradient(circle at 34% 32%,#FFD87A,var(--amber) 58%,#E58A00)}
.nav{order:1;margin-left:auto;display:flex;gap:20px;flex-wrap:wrap}
.nav a{color:#E3ECE6;text-decoration:none;font-size:15px;font-weight:600;padding:4px 0;border-bottom:2px solid transparent}
.nav a:hover,.nav a[aria-current]{color:#fff;border-bottom-color:var(--amber)}
.lang{order:2;background:var(--amber);color:var(--ink);border:0;border-radius:6px;font:inherit;font-size:14px;font-weight:800;padding:7px 14px;cursor:pointer}
.lang:hover{background:#ffc552}
.hero{position:relative;min-height:520px;height:calc(100vh - 150px);max-height:700px;display:flex;align-items:center;overflow:hidden;background:var(--pine)}
.hero picture,.hero picture img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(14,26,20,.94) 0%,rgba(14,26,20,.82) 38%,rgba(14,26,20,.25) 72%,rgba(14,26,20,0) 100%)}
.hero-in{position:relative;z-index:1;padding:0 var(--rail);max-width:calc(760px + var(--rail))}
.hero h1{color:#fff;font-size:clamp(2.1rem,5vw,3.4rem);line-height:1.08;margin:0 0 .4em;letter-spacing:-.02em}
.hero p{color:#E9F0EB;font-size:clamp(1.05rem,1.6vw,1.25rem);margin:0 0 1.4em}
.btn{display:inline-block;background:var(--amber);color:var(--ink);font-weight:800;text-decoration:none;padding:14px 26px;border-radius:8px}
.btn:hover{background:#ffc552;color:var(--ink)}
.btn-dark{background:var(--pine);color:#fff}.btn-dark:hover{background:var(--moss);color:#fff}
.band{padding:56px var(--rail)}
.band-blue{background:var(--sky);color:#fff}.band-blue a{color:#FFE2A3}.band-blue h2{color:#fff;border-color:var(--amber)}
.band-ember{background:var(--ember);color:#fff}.band-ember a{color:#fff}.band-ember h2{color:#fff;border-color:#fff}
h2{font-size:clamp(1.5rem,2.6vw,2rem);line-height:1.2;margin:0 0 .6em;padding-left:14px;border-left:6px solid var(--amber);color:var(--pine)}
h3{font-size:1.2rem;margin:1.6em 0 .4em;color:var(--pine)}
.band-blue h3{color:#fff}
p{margin:0 0 1em}
figure{margin:28px 0}figure img{width:100%;height:auto;border-radius:10px}
figcaption{font-size:.88em;color:var(--muted);padding-top:8px}
.split{display:grid;grid-template-columns:1.25fr 1fr;gap:40px;align-items:start}
@media(max-width:860px){.split{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;margin:20px 0;font-size:.95em;border:2px solid var(--pine)}
th{background:var(--pine);color:#fff;text-align:left;padding:12px 14px;font-size:.85em;letter-spacing:.04em;text-transform:uppercase}
td{padding:12px 14px;border-bottom:1px solid var(--line);background:#fff;color:var(--ink)}
tr:nth-child(even) td{background:#EEF3F0}
.box{border:2px solid var(--sky);background:#E3F1F7;border-radius:10px;padding:20px 22px;margin:24px 0}
.box-warn{border-color:var(--ember);background:#FDEBE3}
.box p:last-child{margin-bottom:0}
.picks{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:22px;margin-top:24px}
.pick{border:2px solid var(--pine);border-top:8px solid var(--amber);border-radius:12px;padding:22px;background:#F2F6F3}
.pick h3{margin-top:0}
.pick .spec{font-size:.92em;color:var(--muted)}
.pick .btn{margin-top:6px}
.related{display:flex;gap:12px;flex-wrap:wrap;margin-top:16px}
.related a{border:2px solid var(--pine);border-radius:100px;padding:8px 18px;text-decoration:none;color:var(--pine);font-weight:700;font-size:.95em;background:#fff}
.related a:hover{background:var(--pine);color:#fff}
.faq h3{margin-top:1.3em}
.disc{font-size:.9em;color:var(--muted);border-top:2px solid var(--line);padding-top:16px;margin-top:30px}
.foot{background:var(--pine);color:#D7E3DB;padding:44px var(--rail) 30px;font-size:15px}
.foot a{color:#fff}
.foot-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:28px}
.foot h4{color:var(--amber);margin:0 0 10px;font-size:15px;letter-spacing:.04em;text-transform:uppercase}
.foot ul{list-style:none;margin:0;padding:0}.foot li{margin:0 0 6px}
.foot .fine{border-top:1px solid rgba(255,255,255,.18);margin-top:26px;padding-top:16px;font-size:13.5px}
.skip{position:absolute;left:-999px}.skip:focus{left:10px;top:10px;z-index:99;background:#fff;padding:8px}
@media(max-width:760px){.site-head{position:static}.head-in{gap:10px 14px}.brand{font-size:17px}.lang{margin-left:auto;padding:6px 12px}.nav{order:3;width:100%;margin:0;flex-wrap:nowrap;overflow-x:auto;gap:18px;padding-bottom:2px;scrollbar-width:none}.nav a{white-space:nowrap;font-size:14.5px}.hero{height:auto;min-height:480px;padding:60px 0}.hero::after{background:linear-gradient(180deg,rgba(14,26,20,.55) 0%,rgba(14,26,20,.85) 55%,rgba(14,26,20,.92) 100%)}.band{padding:40px var(--rail)}table{display:block;overflow-x:auto;font-size:.88em}th,td{padding:10px 10px}}
#google_translate_element{display:none}
body{top:0!important}.goog-te-banner-frame,.skiptranslate iframe{display:none!important}
"""

TRANSLATE_JS = """
(function(){var b=document.getElementById('lang');if(!b)return;
var on=/googtrans=\\/en\\/es/.test(document.cookie);b.textContent=on?'English':'Español';
function load(){window.gtInit=function(){new google.translate.TranslateElement({pageLanguage:'en',includedLanguages:'en,es',autoDisplay:false},'google_translate_element')};
var s=document.createElement('script');s.src='https://translate.google.com/translate_a/element.js?cb=gtInit';document.body.appendChild(s)}
if(on)window.addEventListener('load',load);
b.addEventListener('click',function(){var d=location.hostname;
if(on){document.cookie='googtrans=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT';document.cookie='googtrans=;path=/;domain=.'+d+';expires=Thu, 01 Jan 1970 00:00:00 GMT'}
else{document.cookie='googtrans=/en/es;path=/'}location.reload()})})();
"""

GA_JS = """
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','%s');
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href*="jackery.com"]');if(a){gtag('event','affiliate_click',{link_url:a.href,page:location.pathname});}},true);
(function(){var done=false;function go(){if(done)return;done=true;var s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id=%s';document.head.appendChild(s);}
['scroll','click','touchstart','keydown'].forEach(function(ev){window.addEventListener(ev,go,{once:true,passive:true})});
window.addEventListener('load',function(){setTimeout(go,3500)})})();
""" % (GA, GA)


def webp_set(name):
    """Make WebP copies of /images/<name> and return (srcset, width, height)."""
    src = IMG / name
    im = Image.open(src).convert("RGB")
    w0, h0 = im.size
    WEBP.mkdir(exist_ok=True)
    parts = []
    stem = src.stem
    for w in [w for w in WIDTHS if w < w0] + [w0]:
        out = WEBP / f"{stem}-{w}.webp"
        if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
            im.resize((w, round(h0 * w / w0)), Image.LANCZOS).save(out, "WEBP", quality=78, method=6)
        parts.append(f"/images/w/{stem}-{w}.webp {w}w")
    return ", ".join(parts), w0, h0


def picture(name, alt, sizes, hero=False):
    srcset, w, h = webp_set(name)
    load = 'fetchpriority="high"' if hero else 'loading="lazy" decoding="async"'
    return (f'<picture><source type="image/webp" srcset="{srcset}" sizes="{sizes}">'
            f'<img src="/images/{name}" alt="{html.escape(alt, quote=True)}" width="{w}" height="{h}" {load}></picture>')


def expand_figures(body):
    """Turn <fig src="x.jpg" alt="..." cap="..."> into a full <figure> with WebP srcset."""
    def rep(m):
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(0)))
        cap = f'<figcaption>{attrs["cap"]}</figcaption>' if attrs.get("cap") else ""
        sizes = attrs.get("sizes", "(max-width: 860px) 100vw, 50vw")
        return f'<figure>{picture(attrs["src"], attrs["alt"], sizes)}{cap}</figure>'
    return re.sub(r'<fig\s[^>]*>', rep, body)


def build(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--META\s*(\{.*?\})\s*META-->\s*(.*)", raw, re.S)
    if not m:
        raise SystemExit(f"{path.name}: missing META header")
    meta = json.loads(m.group(1))
    body = expand_figures(m.group(2))
    slug = meta["slug"]
    url = f"{SITE}/{slug}/"
    hero_srcset, _, _ = webp_set(meta["hero"])
    hero_pic = picture(meta["hero"], meta["hero_alt"], "100vw", hero=True)
    nav = "".join(
        f'<a href="{h}"{" aria-current=\"page\"" if h == "/" + slug + "/" else ""}>{t}</a>' for t, h in NAV)
    schema = {
        "@context": "https://schema.org", "@graph": [
            {"@type": "Article", "headline": meta["h1"], "description": meta["description"],
             "dateModified": meta["updated"], "author": {"@type": "Organization", "name": "Dominion Solar Pro"},
             "publisher": {"@type": "Organization", "name": "Dominion Solar Pro", "url": SITE + "/"},
             "mainEntityOfPage": url, "image": f"{SITE}/images/{meta['hero']}"},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": meta["h1"], "item": url}]},
        ]}
    if meta.get("faq"):
        schema["@graph"].append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in meta["faq"]]})
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(meta["title"])}</title>
<meta name="description" content="{html.escape(meta["description"], quote=True)}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(meta["h1"], quote=True)}">
<meta property="og:description" content="{html.escape(meta["description"], quote=True)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/images/{meta["hero"]}">
<link rel="preload" as="image" type="image/webp" imagesrcset="{hero_srcset}" imagesizes="100vw" fetchpriority="high">
<style>{re.sub(r"\s*\n\s*", "", CSS)}</style>
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<script>{GA_JS.strip()}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="scripture">John 3:16</div>
<div class="creed"><em>"I believe the unbelievable, I receive the impossible, because it's doable."</em> &nbsp;&mdash;&nbsp;<b>Jesse Duplantis</b></div>
<header class="site-head"><div class="head-in">
<a class="brand" href="/"><span class="brand-mark" aria-hidden="true"></span>Dominion Solar Pro</a>
<button class="lang" id="lang" type="button" aria-label="Translate this page">Español</button>
<nav class="nav" aria-label="Main">{nav}</nav>
</div></header>
<div id="google_translate_element"></div>
<section class="hero">{hero_pic}<div class="hero-in"><h1>{meta["h1"]}</h1><p>{meta["lede"]}</p><a class="btn" href="{meta.get("cta_href", "#picks")}">{meta.get("cta", "See the setups")}</a></div></section>
<main id="main">
{body.strip()}
</main>
<footer class="foot"><div class="foot-grid">
<div><h4>Dominion Solar Pro</h4><p>Plain-spoken buying guides for Jackery solar generators, power stations and panels. Based in East Texas.</p></div>
<div><h4>Guides</h4><ul>{"".join(f'<li><a href="{h}">{t}</a></li>' for t, h in NAV)}</ul></div>
<div><h4>More</h4><ul><li><a href="/buying-guide.html">Buying guide</a></li><li><a href="/blog/">Blog</a></li><li><a href="/about.html">About</a></li><li><a href="https://www.facebook.com/dominionsolarenergypros" target="_blank" rel="noopener">Facebook</a></li></ul></div>
</div>
<p class="fine"><b>Affiliate disclosure:</b> Dominion Solar Pro is a Jackery affiliate. We earn a commission when you buy through our Jackery links, at no extra cost to you. Specs come from Jackery's published ratings; confirm current specs, stock and price on the product page before you buy.<br>&copy; 2026 Dominion Solar Pro, a Dominion Digital Group brand. East Texas, USA.</p>
</footer>
<script>{TRANSLATE_JS.strip()}</script>
</body>
</html>
"""
    out = ROOT / slug / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out, len(page)


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for p in sorted(PAGES.glob("*.html")):
        if only and p.stem not in only:
            continue
        out, size = build(p)
        print(f"built {out.relative_to(ROOT)}  {size:,} bytes")
