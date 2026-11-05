#!/usr/bin/env python3
"""Build one static multi-page locksmith site per location.

  python3 scripts/build.py            # all locations
  python3 scripts/build.py seattle    # only domains containing "seattle"

Inputs:  template/base.html, template/pages/*.html, template/blog/*.html, template/form.html,
         template/styles.css, data/locations.json
Output:  sites/<domain>/...
"""
import json, re, sys, datetime, shutil, html as htmlmod
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = ROOT / "template"
BASE = (T / "base.html").read_text()
STYLES = (T / "styles.css").read_text().strip()
FORM = (T / "form.html").read_text()
LOCATIONS = json.loads((ROOT / "data" / "locations.json").read_text())
PRODUCTS = json.loads((ROOT / "data" / "products.json").read_text())
PRODUCT_TPL = (T / "product.html").read_text()
REVIEWS_FILE = ROOT / "data" / "reviews.json"
REVIEWS = json.loads(REVIEWS_FILE.read_text()) if REVIEWS_FILE.exists() else {"rating": "", "count": "", "reviews": []}
AREA_TPL = (T / "area.html").read_text()
FAQS = json.loads((ROOT / "data" / "faqs.json").read_text())
BRANDS = json.loads((ROOT / "data" / "brands.json").read_text())


def brands_section(f):
    cats = []
    for b in BRANDS:
        if b["cat"] not in cats:
            cats.append(b["cat"])
    cols = []
    for c in cats:
        items = "".join(f'<li><a href="{htmlmod.escape(b["url"])}" target="_blank" rel="noopener">{htmlmod.escape(b["name"])}</a><span>{htmlmod.escape(b["note"])}</span></li>' for b in BRANDS if b["cat"] == c)
        cols.append(f'      <div class="brandcol"><h3>{htmlmod.escape(c)}</h3><ul>{items}</ul></div>')
    return f"""<section class="seam" aria-labelledby="h-brands">
  <div class="wrap">
    <h2 id="h-brands">Lock brands we install and service in {f['city']}</h2>
    <p>{f['business']} carries, installs, rekeys and repairs hardware from the manufacturers below. Links go to the official manufacturer sites so you can compare models before you call.</p>
    <div class="brandgrid">
{chr(10).join(cols)}
    </div>
  </div>
</section>"""


def autolink_brands(html):
    """Link the first plain-text mention of each brand name (outside tags/links/headings) to the manufacturer site."""
    for b in sorted(BRANDS, key=lambda x: -len(x["name"])):
        name = b["name"]
        pat = re.compile(r"(?<![\w/-])" + re.escape(name) + r"(?![\w-])(?![^<]*>)(?![^<]*</a>)(?![^<]*</h[1-3]>)(?![^<]*</summary>)")
        html, n = pat.subn(f'<a href="{htmlmod.escape(b["url"])}" target="_blank" rel="noopener">{name}</a>', html, count=1)
    return html


def brand_links_inline():
    return ", ".join(f'<a href="{htmlmod.escape(b["url"])}" target="_blank" rel="noopener">{htmlmod.escape(b["name"])}</a>' for b in BRANDS[:9])

IMG_DIR = T / "img"
OUT = ROOT / "sites"

# (ink, signal, signal_ink, paper)
PALETTES = [
    ("#0D1F3C", "#FFD166", "#0D1F3C", "#F1F4F9"),  # midnight + warm gold
    ("#1B2733", "#F2B705", "#1B2733", "#F3F5F7"),  # steel + signal yellow
    ("#14281D", "#B7D94A", "#14281D", "#F2F5EF"),  # forest + lime
    ("#3B1219", "#E8B04B", "#3B1219", "#F7F3F1"),  # burgundy + gold
    ("#202124", "#FF7A1A", "#1B1B1B", "#F4F4F4"),  # charcoal + safety orange
    ("#0F3A3F", "#5FD3C7", "#0F3A3F", "#EFF5F5"),  # deep teal + aqua
    ("#26282B", "#E63946", "#FFFFFF", "#F5F5F5"),  # graphite + red
    ("#123C5A", "#FF8C69", "#123C5A", "#EFF4F8"),  # ocean + coral
    ("#2A1E4A", "#FFB347", "#2A1E4A", "#F4F2F8"),  # royal purple + amber
    ("#2B1D14", "#E39A4F", "#2B1D14", "#F6F2EC"),  # espresso + copper
]


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(v))) for v in rgb)


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def mix(a, b, t):
    return _hex([x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))])


def palette_for(idx):
    ink, signal, signal_ink, paper = PALETTES[idx % len(PALETTES)]
    return {
        "c_ink": ink, "c_ink2": mix(ink, "#FFFFFF", 0.07), "c_ink3": mix(ink, "#FFFFFF", 0.16),
        "c_steel": mix(ink, "#FFFFFF", 0.22), "c_mist": mix(ink, "#FFFFFF", 0.52),
        "c_panel": mix(paper, ink, 0.07), "c_paper": paper, "c_signal": signal,
        "c_signal_hover": mix(signal, "#FFFFFF", 0.14), "c_signal_ink": signal_ink,
        "c_ondark": mix(ink, "#FFFFFF", 0.78),
    }


# Shield with a key: the brand mark. {ink}/{signal} substituted per site.
MARK = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64' aria-hidden='true'><path d='M32 2 58 11v20c0 15-11 26-26 31C17 57 6 46 6 31V11z' fill='{signal}'/><path d='M32 7 53 14.5V31c0 12.5-9 21.7-21 26C20 52.7 11 43.5 11 31V14.5z' fill='{ink}'/><circle cx='32' cy='23' r='8.5' fill='none' stroke='{signal}' stroke-width='4.5'/><path d='M32 31.5V50M32 41h7M32 46.5h5' stroke='{signal}' stroke-width='4.5' stroke-linecap='round'/></svg>"""

LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 160" width="640" height="160" role="img" aria-label="{business}">
<style>@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&amp;family=Barlow:wght@500&amp;display=swap');</style>
<rect width="640" height="160" fill="{ink}"/>
<g transform="translate(30,16) scale(2)"><path d='M32 2 58 11v20c0 15-11 26-26 31C17 57 6 46 6 31V11z' fill='{signal}'/><path d='M32 7 53 14.5V31c0 12.5-9 21.7-21 26C20 52.7 11 43.5 11 31V14.5z' fill='{ink}'/><circle cx='32' cy='23' r='8.5' fill='none' stroke='{signal}' stroke-width='4.5'/><path d='M32 31.5V50M32 41h7M32 46.5h5' stroke='{signal}' stroke-width='4.5' stroke-linecap='round'/></g>
<text x="170" y="76" font-family="'Barlow Condensed','Arial Narrow',sans-serif" font-weight="700" font-size="48" fill="{signal}" letter-spacing="0.5">{city}</text>
<text x="170" y="116" font-family="'Barlow Condensed','Arial Narrow',sans-serif" font-weight="700" font-size="40" fill="#FFFFFF" letter-spacing="0.5">LOCKSMITH SERVICE</text>
<text x="170" y="142" font-family="Barlow,sans-serif" font-weight="500" font-size="13" fill="{mist}" letter-spacing="2.5">SINCE {since} · {cityst} · 24 HOURS · {phone}</text>
</svg>
"""

# slug -> (page template, nav key)
PAGES = {
    "": ("home", "home"),
    "emergency-locksmith": ("emergency", "emergency"),
    "automotive-locksmith": ("auto", "auto"),
    "residential-locksmith": ("residential", "residential"),
    "commercial-locksmith": ("commercial", "commercial"),
    "services": ("services", "services"),
    "service-areas": ("areas", "areas"),
    "about": ("about", "about"),
    "contact": ("contact", "contact"),
    "thank-you": ("thankyou", "contact"),
    "404": ("404", "home"),
}
NAV_KEYS = ["home", "emergency", "auto", "carkey", "residential", "rekey", "commercial", "services", "areas", "blog", "about", "contact"]

FAQ_SCHEMA = """<script type="application/ld+json">
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
{"@type":"Question","name":"How fast can you get to me in {{city}}?","acceptedAnswer":{"@type":"Answer","text":"Most lockouts in {{city}} are reached within 20 to 40 minutes. The dispatcher gives you an arrival time when you call."}},
{"@type":"Question","name":"How much does a locksmith cost in {{city}}?","acceptedAnswer":{"@type":"Answer","text":"It depends on the job. A standard car or house lockout is the most affordable call; car key replacement depends on the key type. You get a firm price before any work starts, and the estimate is free."}},
{"@type":"Question","name":"Can you make a car key if I lost the only one?","acceptedAnswer":{"@type":"Answer","text":"Yes. We cut and program keys from scratch for almost every make and model, including transponder keys and push-to-start fobs, right where the car is. No tow to the dealer."}},
{"@type":"Question","name":"Will you damage my lock or my car?","acceptedAnswer":{"@type":"Answer","text":"No. Lockouts are opened with picks, bypass tools and air wedges, not drills or slim jims, whenever the lock allows it. If drilling is the only option we tell you first."}},
{"@type":"Question","name":"Should I rekey or replace my locks after moving?","acceptedAnswer":{"@type":"Answer","text":"If the hardware is in good shape, rekeying is cheaper and just as secure: the old keys stop working and you get one new key for every door. We replace only locks that are worn, damaged or low-grade."}},
{"@type":"Question","name":"Do you cover the whole {{area_code}} area?","acceptedAnswer":{"@type":"Answer","text":"Yes. Every {{city}} neighborhood plus {{nearby_inline}}. Whether you call it {{nicknames}} or just the {{area_code}}, a technician is usually 20 to 40 minutes away."}},
{"@type":"Question","name":"Are you licensed and insured?","acceptedAnswer":{"@type":"Answer","text":"Yes. {{business}} is licensed and insured, and every technician is background-checked and carries ID."}}
]}
</script>"""

GTM_HEAD = """<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','{gtm}');</script>
<!-- End Google Tag Manager -->"""
GTM_BODY = """<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={gtm}" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>"""

BLOG_DIR = T / "blog"


def blog_posts():
    posts = []
    for fp in sorted(BLOG_DIR.glob("*.html")):
        src = fp.read_text()
        meta = dict(re.findall(r"<!-- (\w+): (.*?) -->", src))
        body = re.sub(r"<!-- \w+: .*? -->\n?", "", src)
        posts.append({"slug": fp.stem, "title": meta["title"], "desc": meta["desc"], "date": meta["date"], "body": body})
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


POSTS = blog_posts()

POST_TPL = """<section class="hero sub" aria-labelledby="h1">
  <div class="wrap">
    <p class="crumb"><a href="/blog/">Blog</a></p>
    <h1 id="h1">{title}</h1>
    <p class="lede">{desc}</p>
    <p class="meta">{datefmt} · {business}</p>
  </div>
  <div class="door" aria-hidden="true"><i></i><i></i></div>
</section>
<section aria-label="Article">
  <div class="wrap two">
    <article class="prose">
{body}
    </article>
    <div>
      <div class="aside">
        <h3>Need a locksmith now?</h3>
        <p>Mobile locksmith across {city} and nearby. Phones answered 24 hours.</p>
        <a class="call" href="tel:+1{phone_digits}">Call {phone}</a>
      </div>
      <div class="aside" style="margin-top:1rem">
        <h3>More from the blog</h3>
        <ul>{others}</ul>
      </div>
    </div>
  </div>
</section>"""

ARTICLE_SCHEMA = """<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BlogPosting","headline":"{title}","description":"{desc}","datePublished":"{date}","dateModified":"{date}","mainEntityOfPage":"https://www.{domain}/blog/{slug}/","author":{{"@type":"Organization","name":"{business}","url":"https://www.{domain}/"}},"publisher":{{"@type":"Organization","name":"{business}","url":"https://www.{domain}/"}}}}
</script>"""

BLOG_INDEX_TPL = """<section class="hero sub" aria-labelledby="h1">
  <div class="wrap">
    <h1 id="h1">Lock and key advice from {city}</h1>
    <p class="lede">Plain answers to the questions {city} drivers, homeowners and business owners ask us most.</p>
  </div>
  <div class="door" aria-hidden="true"><i></i><i></i></div>
</section>
<section aria-label="Articles">
  <div class="wrap">
    <div class="grid">
{cards}
    </div>
  </div>
</section>"""


def datefmt(d):
    return datetime.date.fromisoformat(d).strftime("%B %-d, %Y")


def card(p, f):
    return f'      <div class="svc"><h3><a href="/blog/{p["slug"]}/">{htmlmod.escape(sub(p["title"], f))}</a></h3><p>{htmlmod.escape(sub(p["desc"], f))}</p><a class="more" href="/blog/{p["slug"]}/">Read the article</a></div>'


def render_blog(f):
    out = []
    cards = []
    for p in POSTS:
        pf = dict(f)
        others = "".join(f'<li><a href="/blog/{o["slug"]}/">{htmlmod.escape(sub(o["title"], f))}</a></li>' for o in POSTS if o is not p)
        content = POST_TPL.format(title=htmlmod.escape(sub(p["title"], f)), desc=htmlmod.escape(sub(p["desc"], f)), datefmt=datefmt(p["date"]),
                                  business=f["business"], body=sub(p["body"], f), city=f["city"], phone=f["phone"], phone_digits=f["phone_digits"], others=others)
        pf.update({
            "page_title": htmlmod.escape(sub(p["title"], f) + f" - {f['cityst']} | " + f["business"], quote=True),
            "page_desc": htmlmod.escape(sub(p["desc"], f), quote=True),
            "path": f"/blog/{p['slug']}/",
            "content": content,
            "schema_extra": ARTICLE_SCHEMA.format(title=htmlmod.escape(sub(p["title"], f), quote=True), desc=htmlmod.escape(sub(p["desc"], f), quote=True),
                                                  date=p["date"], domain=f["domain"], slug=p["slug"], business=f["business"]),
        })
        for k in NAV_KEYS:
            pf[f"cur_{k}"] = 'aria-current="page"' if k == "blog" else ""
        out.append((f"/blog/{p['slug']}/", sub(BASE, pf)))
        cards.append(card(p, f))
    pf = dict(f)
    pf.update({
        "page_title": htmlmod.escape(f"Blog - Locksmith {f['cityst']} | {f['business']}", quote=True),
        "page_desc": htmlmod.escape(f"Lock and key advice for {f['city']}: lost car keys, lockouts, rekeying, smart locks and home security.", quote=True),
        "path": "/blog/",
        "content": BLOG_INDEX_TPL.format(city=f["city"], cards="\n".join(cards)),
        "schema_extra": "",
    })
    for k in NAV_KEYS:
        pf[f"cur_{k}"] = 'aria-current="page"' if k == "blog" else ""
    out.append(("/blog/", sub(BASE, pf)))
    return out


ROBOTS = "User-agent: *\nAllow: /\nSitemap: https://www.{domain}/sitemap.xml\n"

SOCIAL_ICONS = {
    "facebook": ("Facebook", "M14 8h3V4h-3c-2.8 0-5 2.2-5 5v2H6v4h3v9h4v-9h3l1-4h-4V9c0-.6.4-1 1-1z"),
    "x": ("X (Twitter)", "M3 3h5l5 7 6-7h3l-7.5 8.6L21 21h-5l-5.3-7.4L4 21H1l8-9.2z"),
    "instagram": ("Instagram", "M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5zm0 2a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3zm5 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm0 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm5-3.5a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"),
    "youtube": ("YouTube", "M22 8.2a3 3 0 0 0-2.1-2.1C18 5.6 12 5.6 12 5.6s-6 0-7.9.5A3 3 0 0 0 2 8.2 31 31 0 0 0 1.6 12 31 31 0 0 0 2 15.8a3 3 0 0 0 2.1 2.1c1.9.5 7.9.5 7.9.5s6 0 7.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .4-3.8 31 31 0 0 0-.4-3.8zM10 15V9l5.2 3z"),
    "tiktok": ("TikTok", "M16.5 2c.3 2.3 1.7 3.9 4 4.1v3.4c-1.5 0-2.9-.5-4-1.3v6.6a5.9 5.9 0 1 1-5.9-5.9c.3 0 .7 0 1 .1v3.5a2.5 2.5 0 1 0 1.5 2.3V2z"),
}


def social_html(social):
    if not social:
        return ""
    out = []
    for k, url in social.items():
        if k not in SOCIAL_ICONS or not url:
            continue
        label, path = SOCIAL_ICONS[k]
        out.append(f'<a href="{htmlmod.escape(url)}" target="_blank" rel="noopener" aria-label="{label}" title="{label}"><svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true"><path d="{path}"/></svg></a>')
    return '<div class="social">' + "".join(out) + "</div>"


def stars(n):
    return '<span class="stars" aria-label="%d out of 5 stars">%s</span>' % (n, "★" * n + "☆" * (5 - n))


def review_cards(revs, f, limit=6):
    cards = []
    for r in revs[:limit]:
        cards.append(
            f'      <blockquote class="rev"><p>{stars(r["stars"])}</p><p class="rev-text">“{htmlmod.escape(r["text"])}”</p>'
            f'<footer><b>{htmlmod.escape(r["name"])}</b> · Google review</footer></blockquote>')
    return "\n".join(cards)


def reviews_section(f, revs=None, heading=None, limit=6):
    revs = revs if revs is not None else REVIEWS["reviews"]
    if not revs:
        return ""
    heading = heading or f"What {f['city']} customers say"
    return f"""<section class="seam reviews" aria-labelledby="h-reviews">
  <div class="wrap">
    <div class="rev-head">
      <h2 id="h-reviews">{heading}</h2>
      <p class="rating"><span class="stars">★★★★★</span> <b>{REVIEWS['rating']}</b> rating · <a href="{REVIEWS['google_url']}" target="_blank" rel="noopener">{REVIEWS['count']} Google reviews</a></p>
    </div>
    <div class="grid revs">
{review_cards(revs, f, limit)}
    </div>
    <p class="rev-cta"><a class="more" href="{REVIEWS['write_url']}" target="_blank" rel="noopener">Leave us a review on Google</a></p>
  </div>
</section>"""


def reviews_for(slug):
    tagged = [r for r in REVIEWS["reviews"] if slug in r.get("tags", [])]
    rest = [r for r in REVIEWS["reviews"] if r not in tagged]
    return (tagged + rest)[:3]


def review_schema():
    if not REVIEWS["reviews"]:
        return ""
    items = ",".join(
        '{"@type":"Review","author":{"@type":"Person","name":"%s"},"reviewRating":{"@type":"Rating","ratingValue":"%d","bestRating":"5"},"reviewBody":"%s"}'
        % (htmlmod.escape(r["name"], quote=True), r["stars"], htmlmod.escape(r["text"], quote=True)) for r in REVIEWS["reviews"][:5])
    return (f',"aggregateRating":{{"@type":"AggregateRating","ratingValue":"{REVIEWS["rating"]}","reviewCount":"{REVIEWS["count"]}","bestRating":"5"}},'
            f'"review":[{items}]')


GALLERY = [
    ("g0.jpg", "{{business}} van on a job in {{city}}", 1400, 1050),
    ("g6.jpg", "Keypad lock installed on a commercial door in {{city}}", 576, 1024),
    ("g1.jpg", "Smart key programmed on site in {{city}}", 675, 1200),
    ("g5.jpg", "New deadbolt and knob installed in {{city}}", 900, 1200),
    ("g4.jpg", "Lock picks and bypass tools used for non-destructive entry", 1400, 1050),
    ("g3.jpg", "Remote-head car key cut and programmed in {{city}}", 576, 1024),
]


def gallery_section(f):
    if not (IMG_DIR / "gallery").exists():
        return ""
    items = "\n".join(
        f'      <figure><img src="/img/gallery/{fn}" alt="{htmlmod.escape(sub(alt, f))}" loading="lazy" width="{w}" height="{h}"><figcaption>{htmlmod.escape(sub(alt, f))}</figcaption></figure>'
        for fn, alt, w, h in GALLERY if (IMG_DIR / "gallery" / fn).exists())
    return f"""<section class="seam" aria-labelledby="h-gallery">
  <div class="wrap">
    <h2 id="h-gallery">Recent work around {f['city']}</h2>
    <div class="gallery">
{items}
    </div>
  </div>
</section>"""


def faq_html(items, f):
    return "\n".join(f'      <details><summary>{htmlmod.escape(sub(q, f))}</summary><p>{htmlmod.escape(sub(a, f))}</p></details>' for q, a in items)


def faq_schema(items, f):
    ents = ",".join('{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}'
                    % (htmlmod.escape(sub(q, f), quote=True), htmlmod.escape(sub(a, f), quote=True)) for q, a in items)
    return '<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[%s]}</script>' % ents


def area_slug(name):
    return "locksmith-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render_area(name, kind, f):
    """kind: 'hood' (neighborhood of the city) or 'city' (nearby city)."""
    slug = area_slug(name)
    path = f"/{slug}/"
    pf = dict(f)
    hoods = [h for h in (f.get("_hoods") or []) if h != name]
    cities = [c for c in (f.get("_nearby") or []) if c != name]
    if kind == "hood":
        where = f"{name}, {f['city']}"
        intro = (f"{name} is one of the {f['city']} neighborhoods {f['business']} covers every day. Our mobile locksmiths are "
                 f"positioned around the city, so a lockout in {name} is usually reached within 20 to 40 minutes, any hour of the day or night.")
        nearby_links = "".join(f'<li><a href="/{area_slug(h)}/">{htmlmod.escape(h)}</a></li>' for h in hoods[:10])
        nearby_title = f"Other {f['city']} neighborhoods we cover"
    else:
        where = f"{name}, {f['st']}"
        intro = (f"{f['business']} is a mobile locksmith based in {f['city']} that also serves {name}, {f['st']}. The van carries everything needed to "
                 f"open a door, cut and program a car key, or rekey a home on the spot, so most jobs in {name} are finished in a single visit.")
        nearby_links = "".join(f'<li><a href="/{area_slug(c)}/">{htmlmod.escape(c)}</a></li>' for c in cities[:10])
        nearby_title = "Nearby cities we also serve"
    faqs = [
        (f"How fast can a locksmith get to {name}?", f"Usually 20 to 40 minutes. {f['business']} runs mobile units around {f['city']} 24 hours a day; the dispatcher gives you an arrival time for {name} when you call {f['phone']}."),
        (f"Do you charge extra to come to {name}?", f"No. {name} is inside our regular service area, so you pay the same rates as anywhere in {f['city']}. You get a firm price before any work starts, and the estimate is free."),
        (f"Can you make a car key in {name} if I lost mine?", f"Yes. We cut and program transponder keys, remote-head keys and push-to-start fobs at your location in {name}, for almost every make and model, with no tow to a dealer."),
        (f"Are you a licensed locksmith serving {name}?", f"Yes. {f['business']} is licensed and insured, in business since {f['since']}, and every technician is background-checked and shows ID on arrival."),
    ]
    pf.update({
        "a_name": htmlmod.escape(name), "a_where": htmlmod.escape(where), "a_intro": htmlmod.escape(intro), "a_slug": slug,
        "a_nearby_title": nearby_title, "a_nearby": nearby_links,
        "a_faq": faq_html(faqs, f),
        "a_reviews": reviews_section(f, REVIEWS["reviews"][:3], heading=f"Reviews from customers around {f['city']}", limit=3),
        "page_title": htmlmod.escape(f"Locksmith {name} | 24 Hour Locksmith near {where} | {f['business']}", quote=True),
        "page_desc": htmlmod.escape(f"24/7 mobile locksmith in {name}: car, home and business lockouts, car key replacement, key fob programming, rekeying and lock installation. Licensed & insured since {f['since']}. Call {f['phone']}.", quote=True),
        "path": path,
        "schema_extra": faq_schema(faqs, f) + '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Service","serviceType":"Locksmith","name":"Locksmith %s","provider":{"@id":"https://www.%s/#business"},"areaServed":{"@type":"%s","name":"%s"},"url":"https://www.%s%s"}</script>'
                        % (htmlmod.escape(name, quote=True), f["domain"], "Place" if kind == "hood" else "City", htmlmod.escape(name, quote=True), f["domain"], path),
    })
    pf["content"] = sub(AREA_TPL, pf)
    for k in NAV_KEYS:
        pf[f"cur_{k}"] = 'aria-current="page"' if k == "areas" else ""
    out = sub(BASE, pf)
    leftover = re.findall(r"{{\w+}}", out)
    if leftover:
        raise SystemExit(f"{f['domain']}{path}: unreplaced {sorted(set(leftover))}")
    return path, out


def wiki_url(loc):
    return loc.get("wiki") or f"https://en.wikipedia.org/wiki/{loc['city'].strip().replace(' ', '_')}"


def joined(items, fallback="the surrounding area"):
    if not items:
        return fallback
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def fields(loc):
    phone = loc["phone"]
    nearby = loc.get("nearby") or []
    hoods = loc.get("neighborhoods") or []
    city = loc["city"].strip()
    pal = palette_for(loc.get("palette", 0))
    gtm = loc.get("gtm", "")
    f = {
        "domain": loc["domain"], "business": loc["business"], "city": city, "state": loc["state"].strip(),
        "st": loc["st"], "zip": loc["zip"], "street": loc.get("street", ""), "phone": phone,
        "phone_digits": re.sub(r"\D", "", phone), "cityst": f"{city}, {loc['st']}", "since": loc["since"],
        "email": loc["email"], "maps_embed": loc.get("maps_embed", ""), "wiki": wiki_url(loc),
        "year": str(datetime.date.today().year),
        "nearby_inline": joined(nearby), "nearby_short": ", ".join(nearby[:4]) if nearby else "the surrounding area",
        "nearby_list": "\n      ".join(f"<li>{htmlmod.escape(n)}</li>" for n in nearby) or "<li>Surrounding communities</li>",
        "hoods_short": ", ".join(hoods[:6]) if hoods else "every neighborhood",
        "hoods_list": "\n      ".join(f"<li>{htmlmod.escape(n)}</li>" for n in hoods) or f"<li>{city}</li>",
        "areas_schema": "".join(f',{{"@type":"City","name":"{htmlmod.escape(n)}"}}' for n in nearby),
        "gtm_head": GTM_HEAD.replace("{gtm}", gtm) if gtm else "",
        "gtm_body": GTM_BODY.replace("{gtm}", gtm) if gtm else "",
        "mark": ('<img class="logo" src="/img/logo.png" alt="{{business}} logo" width="52" height="52">' if (IMG_DIR / "logo.png").exists() else MARK.format(signal=pal["c_signal"], ink=pal["c_ink"])),
        "favicon": "data:image/svg+xml," + MARK.format(signal=pal["c_signal"], ink=pal["c_ink"]).replace("#", "%23").replace("<", "%3C").replace(">", "%3E").replace("'", "%27"),
        "styles": STYLES,
        "social_links": social_html(loc.get("social")),
        "social_sameas": "".join(f',"{htmlmod.escape(u, quote=True)}"' for u in (loc.get("social") or {}).values() if u),
        "sms_digits": re.sub(r"\D", "", loc.get("sms") or phone),
        "rating": REVIEWS.get("rating", ""), "review_count": REVIEWS.get("count", ""),
        "google_url": REVIEWS.get("google_url", "#"), "write_review_url": REVIEWS.get("write_url", "#"),
        "review_schema": review_schema(),
        "_hoods": hoods, "_nearby": nearby,
        "nicknames": joined(loc.get("nicknames") or []), "area_code": loc.get("area_code", ""),
        "region_terms": joined(loc.get("region_terms") or []), "airport": loc.get("airport", ""),
        "alt_names_schema": "".join(f',"{htmlmod.escape(n.replace("the ", ""), quote=True)}"' for n in (loc.get("nicknames") or [])),
        "brand_links": brand_links_inline(),
        "verify_tags": (f'<meta name="msvalidate.01" content="{loc["bing_verify"]}">' if loc.get("bing_verify") else "") + (f'<meta name="google-site-verification" content="{loc["google_verify"]}">' if loc.get("google_verify") else ""),
        "hood_links": "\n      ".join(f'<li><a href="/{area_slug(n)}/">{htmlmod.escape(n)}</a></li>' for n in hoods) or f"<li>{city}</li>",
        "nearby_links": "\n      ".join(f'<li><a href="/{area_slug(n)}/">{htmlmod.escape(n)}</a></li>' for n in nearby) or "<li>Surrounding communities</li>",
        **pal,
    }
    wa = re.sub(r"\D", "", loc.get("whatsapp") or "")
    f["whatsapp_btn"] = (f'<a class="wa" href="https://wa.me/1{wa}?text=Hi%2C%20I%20need%20a%20locksmith%20in%20{city}" target="_blank" rel="noopener">WhatsApp</a>' if wa else "")
    f["reviews_section"] = reviews_section(f)
    f["gallery_section"] = gallery_section(f)
    f["brands_section"] = brands_section(f)
    f["lead_form"] = FORM
    return f


def sub(text, f):
    for _ in range(3):
        for k, v in f.items():
            if isinstance(v, str):
                text = text.replace("{{" + k + "}}", v)
    return text


PRODUCT_SCHEMA = """<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Service","name":"{name}","serviceType":"{name}","provider":{{"@type":"Locksmith","name":"{business}","telephone":"+1-{phone}","url":"https://www.{domain}/"}},"areaServed":{{"@type":"City","name":"{city}"}},"description":"{desc}","image":"https://www.{domain}/img/products/{image}","url":"https://www.{domain}/{slug}/","offers":{{"@type":"Offer","price":"{price}","priceCurrency":"USD","priceSpecification":{{"@type":"PriceSpecification","minPrice":"{price}","priceCurrency":"USD"}}}}}}
</script>"""


def render_product(p, f):
    path = f"/{p['slug']}/"
    pf = dict(f)
    desc = sub(p["desc"], f)
    by_slug = {q["slug"]: q for q in PRODUCTS}
    pfaq = [tuple(x) for x in FAQS.get(p["slug"], [])] + [tuple(x) for x in FAQS.get("_common", [])]
    pfaq = pfaq[:6]
    pf.update({
        "p_faq": faq_html(pfaq, f),
        "p_reviews": reviews_section(f, reviews_for(p["slug"]), heading=f"{p['name']} reviews from {f['city']} customers", limit=3),
        "p_name": htmlmod.escape(p["name"]), "p_desc": htmlmod.escape(desc).replace(f["city"], f'<a href="{f["wiki"]}" rel="noopener" style="color:inherit">{f["city"]}</a>', 1), "p_price": str(p["price"]), "p_image": p["image"],
        "p_bullets": "\n".join(f"        <li>{htmlmod.escape(b)}</li>" for b in p["bullets"]),
        "p_related": "\n".join(f'          <li><a href="/{r}/">{htmlmod.escape(by_slug[r]["name"])}</a></li>' for r in p["related"] if r in by_slug),
        "page_title": htmlmod.escape(f"{p['name']} {f['cityst']} | {f['business']} | {f['phone']}", quote=True),
        "page_desc": htmlmod.escape(desc[:155].rsplit(" ", 1)[0] + " Call " + f["phone"] + ".", quote=True),
        "path": path,
        "schema_extra": PRODUCT_SCHEMA.format(name=htmlmod.escape(p["name"], quote=True), business=f["business"], phone=f["phone"], domain=f["domain"], city=f["city"],
                                              desc=htmlmod.escape(desc, quote=True), image=p["image"], slug=p["slug"], price=p["price"]) + faq_schema(pfaq, f),
    })
    pf["content"] = autolink_brands(sub(PRODUCT_TPL, pf))
    for k in NAV_KEYS:
        pf[f"cur_{k}"] = 'aria-current="page"' if k == "services" else ""
    out = sub(BASE, pf)
    leftover = re.findall(r"{{\w+}}", out)
    if leftover:
        raise SystemExit(f"{f['domain']}{path}: unreplaced {sorted(set(leftover))}")
    return path, out


def render_page(slug, f):
    tpl_name, nav_key = PAGES[slug]
    src = (T / "pages" / f"{tpl_name}.html").read_text()
    title = re.search(r"<!-- title: (.*?) -->", src).group(1)
    desc = re.search(r"<!-- desc: (.*?) -->", src).group(1)
    body = re.sub(r"<!-- (title|desc): .*? -->\n?", "", src)
    path = "/" if slug == "" else f"/{slug}/"
    pf = dict(f)
    pf.update({
        "page_title": htmlmod.escape(sub(title, f), quote=True),
        "page_desc": htmlmod.escape(sub(desc, f), quote=True),
        "path": path,
        "content": autolink_brands(sub(body, f)) if slug not in ("", "about") else sub(body, f),
        "schema_extra": (sub(FAQ_SCHEMA, f) if slug == "" else "") + ('<meta name="robots" content="noindex">' if slug in ("thank-you", "404") else ""),
    })
    for k in NAV_KEYS:
        pf[f"cur_{k}"] = 'aria-current="page"' if k == nav_key else ""
    out = sub(BASE, pf)
    leftover = re.findall(r"{{\w+}}", out)
    if leftover:
        raise SystemExit(f"{f['domain']}{path}: unreplaced {sorted(set(leftover))}")
    return path, out


def build_site(loc, today):
    f = fields(loc)
    d = OUT / f["domain"]
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    urls = []
    f["blog_teasers"] = "\n".join(card(p, f) for p in POSTS[:3])
    for path, out in render_blog(f):
        target = d / path.strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out)
        urls.append(path)
    for p in PRODUCTS:
        path, out = render_product(p, f)
        target = d / p["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out)
        urls.append(path)
    for name in (loc.get("neighborhoods") or []):
        path, out = render_area(name, "hood", f)
        target = d / path.strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out)
        urls.append(path)
    for name in (loc.get("nearby") or []):
        path, out = render_area(name, "city", f)
        target = d / path.strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out)
        urls.append(path)
    if IMG_DIR.exists():
        shutil.copytree(IMG_DIR, d / "img", dirs_exist_ok=True)
    f["product_cards"] = "\n".join(
        f'      <div class="svc pcard"><a href="/{p["slug"]}/"><img src="/img/products/{p["image"]}" alt="{htmlmod.escape(p["name"])} in {f["cityst"]}" loading="lazy" width="500" height="500"></a><h3><a href="/{p["slug"]}/">{htmlmod.escape(p["name"])}</a></h3><p>From ${p["price"]} · {f["cityst"]}</p><a class="more" href="/{p["slug"]}/">{htmlmod.escape(p["name"])} details</a></div>'
        for p in PRODUCTS)
    for slug in PAGES:
        path, out = render_page(slug, f)
        target = d / "404.html" if slug == "404" else (d / slug / "index.html" if slug else d / "index.html")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out)
        if slug not in ("thank-you", "404"):
            urls.append(path)
    (d / "robots.txt").write_text(ROBOTS.format(domain=f["domain"]))
    (d / "logo.svg").write_text(LOGO.format(business=htmlmod.escape(f["business"]), city=htmlmod.escape(f["city"].upper()), since=f["since"],
                                           cityst=htmlmod.escape(f["cityst"].upper()), phone=f["phone"], ink=f["c_ink"], signal=f["c_signal"], mist=f["c_mist"]))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"  <url><loc>https://www.{f['domain']}{u}</loc><lastmod>{today}</lastmod></url>")
    sm.append("</urlset>")
    (d / "sitemap.xml").write_text("\n".join(sm) + "\n")
    return len(urls)


def main():
    flt = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    today = datetime.date.today().isoformat()
    n = pages = 0
    for loc in LOCATIONS:
        if flt and flt not in loc["domain"]:
            continue
        pages += build_site(loc, today)
        n += 1
    shutil.copy(T / "_worker.js", OUT / "_worker.js")
    (OUT / "index.html").write_text(f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/{LOCATIONS[0]["domain"]}/">')
    print(f"built {n} site(s), {pages} pages, into {OUT}")


if __name__ == "__main__":
    main()
