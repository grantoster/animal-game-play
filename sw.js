// The Animal Game offline cache, version 15fb2d7518
const CACHE='animal-game-15fb2d7518';
const CORE=['./','index.html','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const r=e.request; if(r.method!=='GET') return;
  const u=new URL(r.url);
  if(u.origin===location.origin){
    // Network first for the page so updates arrive; fall back to the saved copy offline.
    if(r.mode==='navigate'){
      e.respondWith(fetch(r).then(res=>{ if(res.ok){const cp=res.clone(); caches.open(CACHE).then(c=>c.put('index.html',cp));} return res; }).catch(()=>caches.match('index.html')));
      return;
    }
    e.respondWith(caches.match(r).then(m=>m||fetch(r).then(res=>{ if(res.ok){const cp=res.clone(); caches.open(CACHE).then(c=>c.put(r,cp));} return res; })));
    return;
  }
  if(/fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)){
    e.respondWith(caches.match(r).then(m=>m||fetch(r).then(res=>{ const cp=res.clone(); caches.open(CACHE).then(c=>c.put(r,cp)); return res; }).catch(()=>new Response('',{status:504}))));
  }
});
