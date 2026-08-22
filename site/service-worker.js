const VERSION="v1";
const SHELL_CACHE=`cbt95-shell-${VERSION}`;
const REFERENCE_CACHE=`cbt95-reference-${VERSION}`;
const SHELL_ASSETS=["./","./index.html","./styles.css","./app.js","./search.js","./data-model.js","./manifest.webmanifest","./icon.svg"];
const REFERENCE_ASSETS=["./data/context.bundle.js","./data/search-index.json"];

self.addEventListener("install",event=>{
  event.waitUntil(Promise.all([
    caches.open(SHELL_CACHE).then(cache=>cache.addAll(SHELL_ASSETS)),
    caches.open(REFERENCE_CACHE).then(cache=>cache.addAll(REFERENCE_ASSETS)),
  ]).then(()=>self.skipWaiting()));
});

self.addEventListener("activate",event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(
    keys.filter(key=>key.startsWith("cbt95-")&&![SHELL_CACHE,REFERENCE_CACHE].includes(key)).map(key=>caches.delete(key))
  )).then(()=>self.clients.claim()));
});

function isReference(url){
  return url.pathname.endsWith("/data/context.bundle.js")||url.pathname.endsWith("/data/search-index.json");
}

function isShell(url){
  return ["/","/index.html","/styles.css","/app.js","/search.js","/data-model.js","/manifest.webmanifest","/icon.svg"].some(suffix=>url.pathname.endsWith(suffix));
}

async function notifyFallback(url){
  const clients=await self.clients.matchAll({type:"window",includeUncontrolled:true});
  for(const client of clients) client.postMessage({type:"CBT95_CACHE_FALLBACK",url});
}

async function referenceNetworkFirst(request){
  const cache=await caches.open(REFERENCE_CACHE);
  try{
    const response=await fetch(request,{cache:"no-store"});
    if(response&&response.ok) await cache.put(request,response.clone());
    return response;
  }catch(error){
    const cached=await cache.match(request);
    if(cached){
      await notifyFallback(request.url);
      return cached;
    }
    throw error;
  }
}

async function shellCacheFirst(request){
  const cache=await caches.open(SHELL_CACHE);
  const cached=await cache.match(request);
  if(cached) return cached;
  const response=await fetch(request);
  if(response&&response.ok) await cache.put(request,response.clone());
  return response;
}

self.addEventListener("fetch",event=>{
  const request=event.request;
  if(request.method!=="GET") return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin) return;
  if(isReference(url)){
    event.respondWith(referenceNetworkFirst(request));
    return;
  }
  if(request.mode==="navigate"){
    event.respondWith(shellCacheFirst(new Request("./index.html")));
    return;
  }
  if(isShell(url)) event.respondWith(shellCacheFirst(request));
});
