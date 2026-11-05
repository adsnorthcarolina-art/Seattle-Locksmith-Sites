# Seattle Locksmith Sites

One static website per Seattle-area locksmith domain, all generated from a single locksmith template.

```
data/locations.json      source of truth: business name, phone, email, zip, neighborhoods, nearby cities, palette, GTM id
template/base.html       shared header/footer/schema; template/pages/*.html = each page body
template/form.html       lead form (FormSubmit → the location's email)
template/blog/*.html     blog posts shared by every site
template/styles.css      styles (colors come from the palette in build.py)
scripts/build.py         generates sites/<domain>/ from template + data
sites/<domain>/          ready-to-host static site (index.html, robots.txt, sitemap.xml, logo.svg)
sites/_worker.js         Cloudflare Pages worker: serves sites/<hostname>/, apex → www
```

Build everything: `python3 scripts/build.py`
Build one site: `python3 scripts/build.py seattlelocksmithservice`

Add a site: add an object to `data/locations.json` (give it a different `palette` index), rebuild, commit, then add the domain under Custom domains in the Cloudflare Pages project.

## Pages per site
Home · Emergency locksmith · Automotive locksmith · Car key replacement · Residential locksmith · Lock rekey · Commercial locksmith · All 20 services · Service areas · About · Contact · Blog (3 posts) · Thank-you · 404

## Hosting (Cloudflare Pages)
Pages settings: Framework = None · Build command = *(empty)* · Build output directory = `sites`.
Then add each domain under Custom domains (both `domain.com` and `www.domain.com`).

## Lead form
Forms post to FormSubmit (`https://formsubmit.co/<email>`). The first submission sends an activation email to that address — click "Activate" once and every later lead arrives as an email.

## Analytics
Set `gtm` in `data/locations.json` to a GTM container id (e.g. `GTM-XXXXXXX`) and rebuild; phone clicks push `phone_call` and form submits push `lead_form_submit` to the dataLayer.
