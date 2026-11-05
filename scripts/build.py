"""Builds site/ (GitHub Pages, offline home-screen app) from src/game.html."""
import hashlib, json, os, re
from PIL import Image, ImageDraw
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(ROOT,'src','game.html'); SITE=ROOT  # Pages serves repo root
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world_anything
src=open(SRC,encoding='utf-8').read()
def data(name):
    t=open(os.path.join(ROOT,'src',name),encoding='utf-8').read().strip()
    assert '`' not in t and '${' not in t and '\\' not in t
    return t
pages={'index.html':src.replace('__ANIMALS__',data('animals.tsv')),
       'anything.html':world_anything.transform(src).replace('__ANIMALS__',data('things.tsv'))}
os.makedirs(os.path.join(ROOT,'dist'),exist_ok=True)
open(os.path.join(ROOT,'dist','artifact.html'),'w',encoding='utf-8').write(pages['index.html'])
open(os.path.join(ROOT,'dist','anything.html'),'w',encoding='utf-8').write(pages['anything.html'])
ver=hashlib.sha1((pages['index.html']+pages['anything.html']).encode()).hexdigest()[:10]
def wrap(body):
    body=body.replace('<meta name="claude:viewport-fit-sides" content="cover">\n','')
    title_line,rest=body.split('\n',1)
    head=f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
{title_line}
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Animal Game">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#e7f4ec">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head><body>
'''
    return head+rest+'\n</body></html>\n'
for fn,body in pages.items():
    open(os.path.join(SITE,fn),'w',encoding='utf-8').write(wrap(body))
json.dump({"name":"The Animal Game","short_name":"Animal Game","start_url":"./","scope":"./","display":"standalone",
  "background_color":"#e7f4ec","theme_color":"#e7f4ec","orientation":"any",
  "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png"},{"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}]},
  open(os.path.join(SITE,'manifest.webmanifest'),'w'),indent=1)
sw=f'''// The Animal Game offline cache, version {ver}
const CACHE='animal-game-{ver}';
const CORE=['./','index.html','anything.html','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>{{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()));}});
self.addEventListener('activate',e=>{{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));}});
self.addEventListener('fetch',e=>{{
  const r=e.request; if(r.method!=='GET') return;
  const u=new URL(r.url);
  if(u.origin===location.origin){{
    // Network first for the page so updates arrive; fall back to the saved copy offline.
    if(r.mode==='navigate'){{
      const page=/anything\\.html$/.test(u.pathname)?'anything.html':'index.html';
      e.respondWith(fetch(r).then(res=>{{ if(res.ok){{const cp=res.clone(); caches.open(CACHE).then(c=>c.put(page,cp));}} return res; }}).catch(()=>caches.match(page)));
      return;
    }}
    e.respondWith(caches.match(r).then(m=>m||fetch(r).then(res=>{{ if(res.ok){{const cp=res.clone(); caches.open(CACHE).then(c=>c.put(r,cp));}} return res; }})));
    return;
  }}
  if(/fonts\\.(googleapis|gstatic)\\.com$/.test(u.hostname)){{
    e.respondWith(caches.match(r).then(m=>m||fetch(r).then(res=>{{ const cp=res.clone(); caches.open(CACHE).then(c=>c.put(r,cp)); return res; }}).catch(()=>new Response('',{{status:504}}))));
  }}
}});
'''
open(os.path.join(SITE,'sw.js'),'w').write(sw)
def icon(n):
    S=1024; im=Image.new('RGB',(S,S),'#1e6a4a'); d=ImageDraw.Draw(im)
    d.ellipse((150,80,874,1004),fill='#ffc63a')
    d.polygon([(300,420),(270,230),(430,360)],fill='#8a5c33'); d.polygon([(724,420),(754,230),(594,360)],fill='#8a5c33')
    d.ellipse((260,330,764,900),fill='#a0703f'); d.ellipse((372,600,652,880),fill='#ecd3a3')
    for cx in (412,612):
        d.ellipse((cx-105,410,cx+105,620),fill='#f4e4c1'); d.ellipse((cx-72,443,cx+72,587),fill='#ffffff'); d.ellipse((cx-36,479,cx+36,551),fill='#1b2a23'); d.ellipse((cx+2,486,cx+22,506),fill='#ffffff')
    d.polygon([(472,610),(552,610),(512,690)],fill='#ffc63a')
    d.ellipse((240,320,784,400),fill='#134a33'); d.pieslice((360,170,664,470),180,360,fill='#2a8460'); d.rectangle((362,292,662,326),fill='#ffc63a')
    im.resize((n,n),Image.LANCZOS).save(os.path.join(SITE,f'icon-{n}.png'),optimize=True)
for n in (180,192,512): icon(n)
print('built', ver)
