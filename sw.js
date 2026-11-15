/* Retires the old Varsity app on this address and sends everyone to the new site. */
self.addEventListener('install',function(){self.skipWaiting()});
self.addEventListener('activate',function(e){
  e.waitUntil((async function(){
    try{var ks=await caches.keys();await Promise.all(ks.map(function(k){return caches.delete(k)}))}catch(_){}
    try{await self.registration.unregister()}catch(_){}
    try{var cs=await self.clients.matchAll({type:'window'});cs.forEach(function(c){c.navigate('https://varsityfantasy.github.io/')})}catch(_){}
  })());
});
self.addEventListener('fetch',function(e){e.respondWith(fetch(e.request))});
