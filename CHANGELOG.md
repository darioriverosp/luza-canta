# Historial de versiones

Todas las versiones de **Luza Canta** (antes *Lucesita Canta*). Formato basado en
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y [versionado semántico](https://semver.org/lang/es/):
`MAYOR.MENOR.PARCHE` → MAYOR = cambio grande o que rompe algo, MENOR = funciones nuevas, PARCHE = correcciones.

---

## [2.5.2] — 2026-10-24 · Compartir funciona aunque la app esté recién instalada
### Corregido
- Si el service worker aún no estaba listo (app recién instalada o actualizada), *Compartir → Luza* daba
  "Page not found": la regla de `netlify.toml` solo redirige visitas normales, no envíos. Ahora una Edge
  Function de Netlify (`netlify/edge-functions/recibir.js`) saca el link y abre la portada con él.

## [2.5.1] — 2026-10-24 · Compartir desde YouTube y WhatsApp
### Corregido
- **Compartir → Luza no hacía nada:** el service worker tenía un error de escritura desde la 2.0 (la expresión
  que busca el link había perdido sus `\`) y el navegador no lo instalaba. Ahora, al compartir un video
  desde YouTube, el link se pega solo en la pestaña *YouTube*; y vuelven a llegar los audios de WhatsApp.
- El service worker ya no borra al actualizarse la canción compartida que estaba esperando (`luza-compartido`).

## [2.5.0] — 2026-10-24 · YouTube vuelve a funcionar (RapidAPI)
### Corregido
- **Link de YouTube:** YouTube bloqueaba a Modal por ser un servidor en la nube (*"Sign in to confirm you're
  not a bot"*), con cookies o sin ellas y con cualquier reproductor. Ahora el motor pide el MP3 al servicio
  *YouTube MP3* de RapidAPI (youtube-mp36, plan gratis de 300 canciones/mes, secreto `RAPIDAPI_KEY`);
  si falla, intenta con yt-dlp (cookies y luego reproductores tv, Safari, móvil…).

## [2.4.1] — 2026-10-24 · Motor: yt-dlp siempre al día
### Corregido
- Motor: yt-dlp se actualiza (versión *nightly*) al arrancar cada contenedor. Antes se quedaba con la versión
  del día en que se construyó la imagen de Modal y YouTube terminaba bloqueándolo.
- Motor: `/estado` devuelve aparte un campo `detalle` con el error técnico de yt-dlp (la web no lo muestra);
  sirve para saber si el problema son las cookies (*"Sign in to confirm you're not a bot"*).

## [2.4.0] — 2026-10-23 · Compartir la app
### Agregado
- Apartado **Compartir** encima del pie (en *Cantar* y *Mis canciones*): en el celular abre el menú de
  compartir del teléfono con un mensaje y el enlace; en el ordenador ofrece *WhatsApp* y *Copiar enlace*
  (si el navegador no deja copiar, muestra el enlace para copiarlo a mano).

## [2.3.0] — 2026-10-16 · Créditos, rendimiento y documentación
### Agregado
- Pie de página: *© 2026 Hecho con código y 💙 por Gonzalo Dario Riveros Plaza* con enlace a su web.
- `docs/COMO-FUNCIONA.md`: explicación completa de la arquitectura, la IA, los costos y un guion para video.
- `CHANGELOG.md` (este archivo) y README renovado con tecnologías y versiones.
### Mejorado
- **Rendimiento (PageSpeed):** el CSS va dentro del HTML (`inlineStylesheets: 'always'`), las fuentes Baloo 2 y
  Nunito se sirven desde el propio sitio con `@fontsource` (solo alfabeto latino) y se precargan; caché de
  1 año para `/_astro/*`. Se eliminaron las 2 solicitudes que bloqueaban el dibujado de la página.

## [2.2.0] — 2026-10-16 · Voz guía para ensayar
### Agregado
- **Voz guía:** botones *Sin voz · Bajita 20 % · Media 35 %* que mezclan la voz original bajita debajo de la
  pista karaoke. Compatible con el cambio de tono; los archivos guardados/enviados la incluyen (`-vozguia35`).
### Corregido
- WhatsApp: si preparar el MP3 tarda, Android rechazaba el envío por falta de "toque reciente"; ahora la app
  deja el archivo listo y pide un segundo toque (*✅ Lista · toca para enviar*).
- Motor: borra los archivos temporales de cada canción; error amable si FFmpeg no puede leer el archivo;
  mensaje *"esperando turno"* cuando hay otra canción en proceso; `/pista` responde 404 (no 500) si falló.
- `/recibir` redirige a la portada si se comparte antes de instalar la app; `id` fijo en el manifest.
- Más espacio entre los botones de descarga y el aviso *"Guardada en Mis canciones"*.

## [2.1.0] — 2026-10-16 · Link de YouTube con cookies
### Agregado
- El motor usa las cookies de una cuenta de YouTube (secreto `YT_COOKIES` en GitHub → secreto `luza-youtube`
  en Modal) para que YouTube no bloquee las descargas desde el servidor.

## [2.0.0] — 2026-10-16 · Nuevo nombre: Luza Canta
### Cambiado
- La app pasa a llamarse **Luza Canta**: textos, manifest, ícono en Android (*Luza*), repositorio
  (`luza-canta`), web (`luza-canta.netlify.app`) y motor (`luza-motor`).
- Se mantiene el nombre interno de la base de datos para no perder las canciones guardadas.
- ⚠️ El link anterior `lucesita-canta.netlify.app` dejó de funcionar: hay que reinstalar la app.

## [1.2.0] — 2026-10-16 · Integración con WhatsApp
### Agregado
- **Recibir desde WhatsApp:** Luza aparece en *Compartir* de Android (Web Share Target).
- **Enviar por WhatsApp** la pista karaoke o la voz (Web Share API), con el tono elegido.
- Botones *Guardar en el celular*, ayuda para encontrar audios de WhatsApp y **buscador** en *Mis canciones*.

## [1.1.0] — 2026-10-16 · Motor de IA en Modal
### Cambiado
- El motor de IA se mueve de Hugging Face (Gradio pasó a ser de pago) a **Modal**: API con FastAPI,
  trabajos en segundo plano (`spawn` + consulta de estado) y progreso en un `modal.Dict`.
- Publicación automática del motor con **GitHub Actions** (`.github/workflows/motor.yml`) usando los secretos
  `MODAL_TOKEN_ID` y `MODAL_TOKEN_SECRET`.
- Corre en **CPU** por defecto (sin tarjeta); GPU opcional con la variable `MOTOR_GPU=T4`.
### Corregido
- Se agregó `numpy`, que Demucs necesita en Linux.

## [1.0.0] — 2026-10-16 · Primera versión (Lucesita Canta)
### Agregado
- Web app con **Astro**: flujo de 3 pasos (*Elige tu canción → ¡Quitar la voz! → ¡A cantar!*), diseño colorido
  y responsive pensado para celular.
- Subir MP3 o pegar link de YouTube; **Modo rápido** sin IA (cancelación de fase L − R).
- Cambio de **tono** ±6 semitonos (SoundTouchJS), exportar MP3 (lamejs), **Mis canciones** (IndexedDB).
- **PWA** instalable en Android (manifest, service worker, íconos).
- Motor de IA con **Demucs** (`htdemucs`), FFmpeg y yt-dlp.

[2.3.0]: https://github.com/darioriverosp/luza-canta/releases/tag/v2.3.0
[2.2.0]: https://github.com/darioriverosp/luza-canta/releases/tag/v2.2.0
[2.1.0]: https://github.com/darioriverosp/luza-canta/releases/tag/v2.1.0
[2.0.0]: https://github.com/darioriverosp/luza-canta/releases/tag/v2.0.0
[1.2.0]: https://github.com/darioriverosp/luza-canta/releases/tag/v1.2.0
[1.1.0]: https://github.com/darioriverosp/luza-canta/releases/tag/v1.1.0
[1.0.0]: https://github.com/darioriverosp/luza-canta/releases/tag/v1.0.0
