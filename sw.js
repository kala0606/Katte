/* Katte service worker — offline-first app shell.
   Bump CACHE when any precached file changes to roll the cache over. */
const CACHE = "katte-v1";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./srishti-sun.png",
  "./icon.svg",
  "./icon-192.png",
  "./icon-512.png",
  "./apple-touch-icon.png",
];

self.addEventListener("install", e => {
  // cache the shell; skipWaiting so a new version takes over promptly
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;                    // bot /ask is POST — never touch it
  const url = new URL(req.url);

  // Google Fonts (CSS + font files): cache-first so the app looks right offline
  if (url.hostname.endsWith("googleapis.com") || url.hostname.endsWith("gstatic.com")) {
    e.respondWith(
      caches.open(CACHE).then(c =>
        c.match(req).then(hit => hit || fetch(req).then(res => { c.put(req, res.clone()); return res; })))
    );
    return;
  }

  // same-origin app assets: cache-first, fall back to network, then to the shell
  if (url.origin === self.location.origin) {
    e.respondWith(
      caches.match(req).then(hit => hit ||
        fetch(req).then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy));
          return res;
        }).catch(() => caches.match("./index.html")))
    );
    return;
  }
  // anything else (e.g. the bot tunnel origin): straight to network, no caching
});
