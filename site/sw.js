// Offline cache for the static site. build_site.py fills in the version placeholders below (a hash of
// every shipped file) and the file list; a new deploy therefore has a new cache name, and the old
// cache is dropped on activate. Stale-while-revalidate: answer from the cache whenever possible
// (so the reader works offline) and refresh it in the background.
const CACHE = "regreader-959e6ad90435";
const FILES = ["./", "app.js", "data/fsa-basel-cap-jp.js", "data/index.js", "data/jp-banking-act.js", "data/jp-fiea-enforcement-order.js", "data/jp-fiea.js", "data/jp-mof-consolidated-fs-regulation.js", "data/jp-payment-services-act.js", "data/jp-tlac-notification.js", "icon-180.png", "icon-192.png", "icon-512.png", "icon-maskable-512.png", "index.html", "manifest.webmanifest", "style.css"];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(caches.open(CACHE).then(async (c) => {
    const hit = await c.match(e.request, { ignoreSearch: true });
    const net = fetch(e.request).then((r) => { if (r.ok) c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  }));
});
