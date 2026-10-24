# ✨ Luza Canta

**Quita la voz a tus canciones y ¡a cantar!** 🎤 Web app de karaoke para un club de canto: recibe una canción
(MP3, link de YouTube o compartida desde WhatsApp), la separa con **inteligencia artificial** en *pista karaoke*
y *solo voz*, y permite cambiar el tono, ensayar con voz guía, guardar y enviar el resultado por WhatsApp.
Se instala en Android como una app (PWA).

👉 **App:** https://luza-canta.netlify.app
📖 **Cómo funciona todo (arquitectura, IA, costos):** [docs/COMO-FUNCIONA.md](docs/COMO-FUNCIONA.md)
📝 **Versiones:** [CHANGELOG.md](CHANGELOG.md) · versión actual **2.3.0**

---

## Funciones
| | |
|---|---|
| 🎵 **Elegir canción** | Subir MP3/M4A/WAV, pegar un link de YouTube o *Compartir → Luza* desde WhatsApp |
| 🪄 **Quitar la voz con IA** | Demucs (`htdemucs`) en la nube; devuelve pista karaoke + voz sola |
| ⚡ **Modo rápido** | Sin IA ni internet, al instante en el celular (cancelación de fase) |
| 🎧 **Voz guía** | La voz original bajita (20 % / 35 %) debajo de la pista para aprender la melodía |
| 🎛️ **Tono** | Subir o bajar hasta 6 semitonos sin cambiar la velocidad |
| 💬 **WhatsApp** | Enviar la pista o la voz directo a WhatsApp |
| ⬇️ **Guardar** | Descargar el MP3 al celular |
| 📚 **Mis canciones** | Historial guardado en el celular, con buscador |
| 📲 **Instalable** | PWA: ícono en Android, pantalla completa, aparece en *Compartir* |

## Arquitectura
```
Celular (PWA Astro) ──► Netlify (archivos de la web)
      │  sube canción / link            ▲ baja 2 MP3
      ▼                                 │
Modal (Python) ── FastAPI ─► procesar(): yt-dlp → FFmpeg → Demucs (PyTorch)
      ▲
GitHub Actions ── publica motor/modal_app.py (secretos: MODAL_TOKEN_ID, MODAL_TOKEN_SECRET, YT_COOKIES)
```
Explicación completa en [docs/COMO-FUNCIONA.md](docs/COMO-FUNCIONA.md).

## Tecnologías y versiones
**Web (frontend)**
| Tecnología | Versión | Uso |
|---|---|---|
| [Astro](https://astro.build) | 7.4.0 | Genera el sitio estático (HTML, CSS, JS) |
| HTML · CSS · JavaScript / TypeScript | — | Interfaz y lógica |
| [SoundTouchJS](https://github.com/cutterbl/SoundTouchJS) | 0.3.0 | Cambio de tono |
| [@breezystack/lamejs](https://www.npmjs.com/package/@breezystack/lamejs) | 1.2.7 | Codificar MP3 |
| [idb-keyval](https://github.com/jakearchibald/idb-keyval) | 6.3.0 | Guardar canciones (IndexedDB) |
| [@fontsource](https://fontsource.org) Baloo 2 · Nunito | 5.3.0 | Fuentes propias |
| Web Audio API · Service Worker · Web Share API | navegador | Audio, PWA, WhatsApp |
| sharp (desarrollo) | 0.35.5 | Generar íconos |
| Node.js (desarrollo) | 24 | Construir el sitio |

**Motor de IA (backend)**
| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.11 | Lenguaje del motor |
| [Modal](https://modal.com) | 1.6 | Nube serverless (contenedores por demanda) |
| [Demucs](https://github.com/adefossez/demucs) (`htdemucs`) | 4.1.0 | IA que separa la voz |
| [PyTorch](https://pytorch.org) | última | Ejecuta la red neuronal |
| [FastAPI](https://fastapi.tiangolo.com) | última | API web |
| [FFmpeg](https://ffmpeg.org) | la de Debian | Leer y convertir audio |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) + Deno | última | Bajar audio de YouTube |

**Infraestructura:** GitHub (código, Actions, Secrets) · Netlify (web) · Modal (IA).

## Estructura
```
luza-canta/
├─ src/
│  ├─ layouts/Base.astro       molde común: fondo, logo, menú, ajustes, pie de página
│  ├─ pages/index.astro        pasos 1-2-3 (elegir, quitar la voz, ¡a cantar!)
│  ├─ pages/historial.astro    Mis canciones + buscador
│  ├─ scripts/                 motor.js · modoRapido.js · tono.js · reproductor.js · audio.js · historial.js
│  └─ styles/global.css        diseño
├─ public/                     manifest.webmanifest · sw.js · icons/
├─ motor/modal_app.py          motor de IA (Modal + FastAPI + Demucs + FFmpeg + yt-dlp)
├─ .github/workflows/motor.yml publica el motor en Modal
├─ docs/COMO-FUNCIONA.md       documentación completa
└─ CHANGELOG.md                historial de versiones
```

---

## Instalación y publicación

### 1 · Motor de IA en Modal (sin instalar Python)
1. Crea una cuenta en **https://modal.com**.
2. Modal → **Settings → API Tokens → New Token**; copia `Token ID` y `Token Secret` (sin pegarlos en chats).
3. GitHub → **Settings → Secrets and variables → Actions → New repository secret**:
   `MODAL_TOKEN_ID` y `MODAL_TOKEN_SECRET`.
4. GitHub → **Actions → Publicar motor en Modal → Run workflow** (la primera vez tarda 5-10 min).
5. Abre `https://TU-USUARIO--luza-motor.modal.run`: si dice `"ok": true`, funciona.

> 💡 En Modal pon un **límite de gasto** (*Settings → Usage and Billing*). El motor procesa una canción a la vez
> y se apaga solo a los 2 minutos sin uso (dormido no cobra).

### 2 · La web en Netlify (o Vercel)
- **Netlify:** *Add new site → Import an existing project → GitHub → luza-canta → Deploy* (usa `netlify.toml`).
- **Vercel:** *vercel.com/new → luza-canta → Deploy* (usa `vercel.json`).
- Variable opcional `PUBLIC_MOTOR_URL` con la dirección del motor (por defecto
  `https://darioriverosp--luza-motor.modal.run`; también se puede cambiar en la app, **⚙️ Ajustes**).

### 3 · Instalar en Android
Abrir la web en **Chrome** → botón amarillo **Instalar** (o menú ⋮ → *Agregar a pantalla principal*).
Si ya estaba instalada una versión anterior, desinstalarla y volver a instalar.

## Link de YouTube
YouTube bloquea las descargas desde servidores en la nube como Modal. Por eso el motor pide el MP3 al servicio
**YouTube MP3** de RapidAPI ([youtube-mp36](https://rapidapi.com/niketagup/api/youtube-mp36)), que baja desde
sus propios servidores. Plan gratis *Basic*: **300 canciones al mes** con límite fijo (no cobra de más).
1. RapidAPI → *YouTube MP3* → **Subscribe** → plan *Basic* ($0) → copiar la `X-RapidAPI-Key`.
2. GitHub → Secrets → `RAPIDAPI_KEY` con esa clave.
3. **Actions → Publicar motor en Modal → Run workflow**.

Si RapidAPI falla (sin cuota, servicio caído), el motor intenta igual con yt-dlp. Para saber qué pasó, la
respuesta de `/estado/{id}` trae un campo `detalle` con el error técnico.

### Cookies (respaldo, opcional)
yt-dlp puede usar las cookies de una **cuenta de Google secundaria** (nunca la principal), aunque YouTube
las invalida en pocos días:
1. Ventana privada → iniciar sesión → `youtube.com/robots.txt` → exportar con la extensión *Get cookies.txt LOCALLY*
   → cerrar la ventana **sin cerrar sesión**.
2. GitHub → Secrets → `YT_COOKIES` con el contenido del archivo.
3. **Actions → Publicar motor en Modal → Run workflow**.

Si vuelve a salir *"YouTube no dejó bajar esta canción"*, las cookies vencieron: repetir los 3 pasos.
**Nunca pegues cookies ni llaves en un chat ni en el código.**

## CPU o GPU
Por defecto el motor usa **CPU** (no requiere tarjeta en Modal; ~2-4 min por canción). Con tarjeta registrada
en Modal se puede usar **GPU** (menos de 1 minuto): GitHub → *Settings → Secrets and variables → Actions →
Variables* → `MOTOR_GPU = T4` → *Run workflow*.

## Costos
| Servicio | Costo |
|---|---|
| Netlify · GitHub · librerías de código abierto | $0 |
| Modal | Por segundo de uso, solo mientras procesa. ~1 ¢ por canción (aprox.). $1/mes gratis sin tarjeta · $30/mes con tarjeta |

## Desarrollo
```bash
npm install
npm run dev        # http://localhost:4321
npm run build      # genera dist/
npm run iconos     # regenera los PNG desde public/icons/icono.svg
npx netlify-cli deploy --prod --dir dist   # publicar en Netlify
```

---

Úsala para uso personal y del club, respetando los derechos de autor y los términos de servicio de YouTube.

© 2026 Hecho con código y 💙 por [Gonzalo Dario Riveros Plaza](https://darioriverosp.netlify.app/)
