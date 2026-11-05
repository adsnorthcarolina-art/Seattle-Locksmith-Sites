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
        "gtm_head": GTM_HEAD.format(gtm=gtm) if gtm else "",
        "gtm_body": GTM_BODY.format(gtm=gtm) if gtm else "",
        "mark": ('<img class="logo" src="/img/logo.png" alt="{{business}} logo" width="52" height="52">' if (IMG_DIR / "logo.png").exists() else MARK.format(signal=pal["c_signal"], ink=pal["c_ink"])),
        "favicon": "data:image/svg+xml," + MARK.format(signal=pal["c_signal"], ink=pal["c_ink"]).replace("#", "%23").replace("<", "%3C").replace(">", "%3E").replace("'", "%27"),
        "styles": STYLES,
        **pal,
    }
    f["lead_form"] = FORM
    return f


def sub(text, f):
    for _ in range(3):
        for k, v in f.items():
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
    pf.update({
        "p_name": htmlmod.escape(p["name"]), "p_desc": htmlmod.escape(desc), "p_price": str(p["price"]), "p_image": p["image"],
        "p_bullets": "\n".join(f"        <li>{htmlmod.escape(b)}</li>" for b in p["bullets"]),
        "p_related": "\n".join(f'          <li><a href="/{r}/">{htmlmod.escape(by_slug[r]["name"])}</a></li>' for r in p["related"] if r in by_slug),
        "page_title": htmlmod.escape(f"{p['name']} {f['cityst']} | {f['business']} | {f['phone']}", quote=True),
        "page_desc": htmlmod.escape(desc[:155].rsplit(" ", 1)[0] + " Call " + f["phone"] + ".", quote=True),
        "path": path,
        "schema_extra": PRODUCT_SCHEMA.format(name=htmlmod.escape(p["name"], quote=True), business=f["business"], phone=f["phone"], domain=f["domain"], city=f["city"],
                                              desc=htmlmod.escape(desc, quote=True), image=p["image"], slug=p["slug"], price=p["price"]),
    })
    pf["content"] = sub(PRODUCT_TPL, pf)
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
        "content": sub(body, f),
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
