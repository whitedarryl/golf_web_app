const CACHE_NAME = "golf-scorecard-v1";
const ASSETS = [
    "/",
    "/static/css/styles.css",
    "/static/js/script.js"
];

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
    );
});

self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(response => response || fetch(event.request))
    );
});
