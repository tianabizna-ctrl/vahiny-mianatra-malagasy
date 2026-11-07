/* Offline cache for a static app: shell on install, recordings on first play. */
var VERSION = 'salama-v3.3.0';
var SHELL = [
  './',
  './index.html',
  './styles.css',
  './app.js',
  './manifest.webmanifest',
  './data/content.js',
  './js/core.js',
  './js/speech.js',
  './js/ui.js',
  './js/views/today.js',
  './js/views/course.js',
  './js/views/session.js',
  './js/views/review.js',
  './js/views/quiz.js',
  './js/views/words.js',
  './js/views/library.js',
  './js/views/progress.js',
  './js/views/settings.js',
  './media/icon.svg',
  './media/icon-192.png',
  './media/icon-512.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(VERSION).then(function (cache) {
      // Cache each file on its own: one missing asset must not cancel the whole
      // install, or the app silently loses its offline copy.
      return Promise.all(SHELL.map(function (url) {
        return cache.add(url).catch(function () { return null; });
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (key) { return key !== VERSION; })
        .map(function (key) { return caches.delete(key); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (request.method !== 'GET') return;

  var url = new URL(request.url);
  if (url.origin !== location.origin) return;

  // Recordings are large: cache them the first time they are played.
  if (request.url.indexOf('/media/audio/') !== -1) {
    event.respondWith(
      caches.match(request).then(function (hit) {
        return hit || fetch(request).then(function (response) {
          var copy = response.clone();
          caches.open(VERSION).then(function (cache) { cache.put(request, copy); });
          return response;
        });
      })
    );
    return;
  }

  // Navigations and the shell: serve from cache first, then refresh.
  event.respondWith(
    caches.match(request).then(function (cached) {
      var network = fetch(request).then(function (response) {
        if (response && response.status === 200) {
          var copy = response.clone();
          caches.open(VERSION).then(function (cache) { cache.put(request, copy); });
        }
        return response;
      }).catch(function () {
        return cached || caches.match('./index.html');
      });
      return cached || network;
    })
  );
});
