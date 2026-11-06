// Cloudflare Pages (advanced mode): serve one site per hostname from sites/<domain>/
const DEFAULT = "seattlelocksmithservice.com";
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    let host = url.hostname.toLowerCase();
    const isPagesDev = host.endsWith(".pages.dev");
    // Production preview host -> canonical domain (avoid duplicate indexing). Keep deploy previews (<hash>.project.pages.dev) working.
    if (host === "seattle-locksmith-sites.pages.dev") {
      url.hostname = "www." + DEFAULT;
      return Response.redirect(url.toString(), 301);
    }
    if (!isPagesDev && !host.startsWith("www.")) {
      url.hostname = "www." + host;
      return Response.redirect(url.toString(), 301);
    }
    host = host.replace(/^www\./, "");
    const site = isPagesDev ? DEFAULT : host;
    // Retired area pages (seattlelocksmithservice.com only) -> service areas index
    if (site === DEFAULT && /^\/locksmith-(redmond|mercer-island|tukwila|seatac|kent|edmonds|issaquah|federal-way|everett)\/?$/.test(url.pathname)) {
      url.pathname = "/service-areas/";
      return Response.redirect(url.toString(), 301);
    }
    // Old WordPress URLs still linked from GBP / directories
    const OLD = { "/contact-us/": "/contact/", "/contact-us": "/contact/", "/about-us/": "/about/", "/about-us": "/about/", "/services": "/services/", "/blog": "/blog/", "/car-locksmith": "/automotive-locksmith/", "/car-locksmith/": "/automotive-locksmith/", "/automotive": "/automotive-locksmith/", "/residential": "/residential-locksmith/", "/commercial": "/commercial-locksmith/", "/emergency": "/emergency-locksmith/" };
    if (OLD[url.pathname]) {
      url.pathname = OLD[url.pathname];
      return Response.redirect(url.toString(), 301);
    }
    // Directory URLs without a trailing slash: redirect ourselves (ASSETS would redirect to the internal /<site>/ path)
    if (!url.pathname.endsWith("/") && !/\.[a-z0-9]+$/i.test(url.pathname)) {
      url.pathname += "/";
      return Response.redirect(url.toString(), 301);
    }
    const assetUrl = new URL(request.url);
    assetUrl.pathname = "/" + site + url.pathname;
    const res = await env.ASSETS.fetch(new Request(assetUrl.toString(), request));
    if (res.ok && url.pathname.startsWith("/img/")) {
      // public images: allow cross-origin reads (used when uploading product photos to Google Business Profile)
      const h = new Headers(res.headers);
      h.set("Access-Control-Allow-Origin", "*");
      return new Response(res.body, { status: res.status, headers: h });
    }
    if (res.status === 404) {
      const nf = await env.ASSETS.fetch(new Request(new URL("/" + site + "/404.html", request.url).toString(), request));
      if (nf.ok) return new Response(nf.body, { status: 404, headers: nf.headers });
    }
    return res;
  },
};
