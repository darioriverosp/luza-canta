// Service worker de Luza Canta: permite instalarla y abrirla aunque haya mala señal.
const CACHE = 'luza-v4';
const COMPARTIDO = 'luza-compartido';
const BASICOS = ['/', '/historial', '/manifest.webmanifest', '/icons/icono-192.png', '/icons/icono.svg'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(BASICOS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE && k !== COMPARTIDO).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Cuando desde WhatsApp (u otra app) tocan "Compartir → Luza", llega aquí la canción o el link
async function recibir(req) {
  const datos = await req.formData();
  const archivo = datos.get('audio');
  if (archivo && archivo.size) {
    const cache = await caches.open(COMPARTIDO);
    await cache.put('/compartido', new Response(archivo, {
      headers: { 'Content-Type': archivo.type || 'audio/mpeg', 'X-Nombre': encodeURIComponent(archivo.name || 'Canción') },
    }));
    return Response.redirect('/?compartido=1', 303);
  }
  const texto = `${datos.get('url') || ''} ${datos.get('text') || ''}`;
  // YouTube manda el link dentro de "text" (p. ej. "https://youtu.be/abc?si=…"); WhatsApp a veces en "url"
  const link = texto.match(/https?:\/\/\S+/);
  return Response.redirect(link ? `/?link=${encodeURIComponent(link[0])}` : '/', 303);
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method === 'POST' && url.origin === location.origin && url.pathname === '/recibir') {
    e.respondWith(recibir(req));
    return;
  }
  if (req.method !== 'GET' || url.origin !== location.origin) return;

  // Páginas: primero internet, si no hay, la copia guardada
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req)
        .then((r) => {
          const copia = r.clone();
          caches.open(CACHE).then((c) => c.put(req, copia));
          return r;
        })
        .catch(() => caches.match(req).then((r) => r || caches.match('/')))
    );
    return;
  }

  // Archivos de la app (tienen nombre único): primero la copia guardada
  e.respondWith(
    caches.match(req).then(
      (r) =>
        r ||
        fetch(req).then((res) => {
          if (res.ok) {
            const copia = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copia));
          }
          return res;
        })
    )
  );
});
