"""Per-site opening hours.

The template is written for 24/7 locksmiths. A location with "hours" in data/locations.json, e.g.
    "hours": {"opens": "07:00", "closes": "23:00"}
gets every round-the-clock claim in its built pages rewritten to those hours (schema, titles, copy, FAQ),
so the site matches its Google Business Profile. Sites without "hours" are untouched.
"""
import re
from pathlib import Path


def _fmt(hhmm):
    h, m = map(int, hhmm.split(":"))
    suf = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}{':%02d' % m if m else ''} {suf}"


def rules(hours):
    o, c = _fmt(hours["opens"]), _fmt(hours["closes"])
    span = f"{o}–{c}"          # 7 AM–11 PM
    words = f"{o} to {c}"      # 7 AM to 11 PM
    return [
        # schema.org
        (r'"opens":"00:00","closes":"23:59"', f'"opens":"{hours["opens"]}","closes":"{hours["closes"]}"'),
        # FAQ
        (r"Are you open 24 hours\?", "What are your hours?"),
        (r"Yes\. ([^.]+?) answers the phone and dispatches technicians 24 hours a day, 7 days a week, including holidays\. Call ([^ ]+) any time\.",
         rf"\1 answers the phone and dispatches technicians {words}, 7 days a week, including holidays. Call \2 during those hours."),
        (r"We are open 24 hours and quote the same way at 3 a\.m\. as at 3 p\.m\.", f"We are open {words} every day and quote the same way at 10 p.m. as at 10 a.m."),
        (r"We are open 24 hours and quote the same way at any hour\.", f"We are open {words} every day and quote the same way at every hour we are open."),
        (r"your apartment at 2 a\.m\.", "your apartment late at night"),
        (r"From a 2 a\.m\. lockout", "From a late-night lockout"),
        # names / titles
        (r"24/7 Emergency Lockout Service", "Emergency Lockout Service"),
        (r"24/7 emergency lockout service", "emergency lockout service"),
        (r"24/7 emergency lockout", "emergency lockout"),
        (r"Emergency lockout, 24/7", f"Emergency lockout, {span}"),
        (r"Locksmith 24/7 \|", "Locksmith |"),
        (r"24/7 mobile locksmith", "mobile locksmith"),
        (r"24-hour emergency locksmith", "emergency locksmith"),
        (r"24-hour emergency lockout", "emergency lockout"),
        (r"24-hour lockout service", "same-day lockout service"),
        (r"24-hour mobile locksmith", "mobile locksmith"),
        (r"for a 24-hour locksmith in", "for a mobile locksmith in"),
        (r"24-hour locksmith", "locksmith"),
        # sentences
        (r"24 hours a day, 7 days a week", f"{words}, 7 days a week"),
        (r"Open 24 hours a day, including nights, weekends and holidays", f"Open {words} every day, including weekends and holidays"),
        (r"Open 24 hours, 7 days a week", f"Open {span}, 7 days a week"),
        (r"24 hours, 7 days", f"{span}, 7 days"),
        (r"Phones are answered 24 hours a day", f"Phones are answered from {words}"),
        (r"(runs mobile units around [^.;]+?) 24 hours a day", rf"\1 from {words}"),
        (r"is available 24 hours a day across", f"is available {span}, every day, across"),
        (r"All available 24 hours a day across", f"All available {span}, every day, across"),
        (r"Call now, 24 hours a day", f"Call now, open {span}"),
        (r"Call, 24 hours a day", f"Call, {span} daily"),
        (r"any hour of the day or night", f"any time from {words}"),
        (r"any hour, every day of the year", f"{words}, every day of the year"),
        (r"any hour, any day", f"{span}, every day"),
        (r"at any hour", f"any time from {words}"),
        (r"Lockouts we handle, any hour", "Lockouts we handle"),
        (r"Opened without damage, any hour", "Opened without damage"),
        (r", any hour", f", {span}"),
        (r"Open 24 hours", f"Open {span}"),
        (r"24 HOURS", span.upper()),
        (r"24 hours a day", f"{words}"),
        (r"24 hours", span),
        (r"24/7", span),
    ]


# Text about scam call-centres that quotes their ad names; keep it as written.
_KEEP = [r"Locksmith [A-Z][A-Za-z .]* 24/7"]


_STARTS = re.compile(r'(?:>|="|":"|<title>|\. |\| )\s*$')


def _cap(m, repl):
    """Expand the replacement; when the matched text began with "24" (no case of its own) and sits at
    the start of a heading, title, attribute or sentence, capitalise what replaces it."""
    out = m.expand(repl)
    if m.group(0)[:2] == "24" and out[:1].islower() and _STARTS.search(m.string[max(0, m.start() - 12):m.start()]):
        out = out[0].upper() + out[1:]
    return out


def apply(site_dir: Path, hours):
    if not hours:
        return
    rs = [(re.compile(p), r) for p, r in rules(hours)]
    keep = [re.compile(k) for k in _KEEP]
    for f in site_dir.rglob("*"):
        if f.suffix not in (".html", ".xml", ".txt", ".svg", ".json") or not f.is_file():
            continue
        s = f.read_text()
        held = []

        def hold(m):
            held.append(m.group(0))
            return f"\x00{len(held) - 1}\x00"
        for k in keep:
            s = k.sub(hold, s)
        for p, r in rs:
            s = p.sub(lambda m, p=p, r=r: _cap(m, r), s)
        s = re.sub(r"\x00(\d+)\x00", lambda m: held[int(m.group(1))], s)
        f.write_text(s)
