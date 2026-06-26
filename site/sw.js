/* Service worker do Bíblia em Contexto — gerado por build.py. Não editar à mão. */
var VERSION = 'f02aab3b';
var SHELL_CACHE = 'bec-shell-' + VERSION;
var PAGE_CACHE  = 'bec-pages-'  + VERSION;
// app-shell mínimo (relativo ao escopo do SW = raiz do site)
var SHELL = [
  './',
  './index.html',
  './offline/',
  './manifest.webmanifest',
  './assets/styles.css?v=' + VERSION,
  './assets/app.js?v=' + VERSION,
  './assets/study.js?v=' + VERSION,
  './data/hebrew-lexicon.json'
];

self.addEventListener('install', function(e){
  e.waitUntil(
    caches.open(SHELL_CACHE).then(function(c){
      // addAll falha tudo se um item falhar; tolera ausências com Promise.allSettled-like
      return Promise.all(SHELL.map(function(u){
        return c.add(u).catch(function(){});
      }));
    }).then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.map(function(k){
        if(k !== SHELL_CACHE && k !== PAGE_CACHE) return caches.delete(k);
      }));
    }).then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function(e){
  var req = e.request;
  if(req.method !== 'GET') return;
  var url = new URL(req.url);
  // só tratamos requisições da mesma origem; terceiros (fontes/imagens) passam direto
  if(url.origin !== self.location.origin) return;

  // navegações (HTML): rede primeiro, cai para cache e, por fim, página offline
  if(req.mode === 'navigate'){
    e.respondWith(
      fetch(req).then(function(res){
        var copy = res.clone();
        caches.open(PAGE_CACHE).then(function(c){ c.put(req, copy); });
        return res;
      }).catch(function(){
        return caches.match(req).then(function(hit){
          return hit || caches.match('./offline/') || caches.match('./index.html');
        });
      })
    );
    return;
  }

  // assets versionados (?v=) são imutáveis: cache primeiro
  if(url.search.indexOf('v=') > -1){
    e.respondWith(
      caches.match(req).then(function(hit){
        return hit || fetch(req).then(function(res){
          var copy = res.clone();
          caches.open(SHELL_CACHE).then(function(c){ c.put(req, copy); });
          return res;
        });
      })
    );
    return;
  }

  // demais (json de dados, imagens locais): stale-while-revalidate
  e.respondWith(
    caches.match(req).then(function(hit){
      var net = fetch(req).then(function(res){
        var copy = res.clone();
        caches.open(PAGE_CACHE).then(function(c){ c.put(req, copy); });
        return res;
      }).catch(function(){ return hit; });
      return hit || net;
    })
  );
});
