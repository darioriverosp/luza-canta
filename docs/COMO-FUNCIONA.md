# 🎤 Cómo funciona Luza Canta (explicado de punta a punta)

Guía para entender, explicar y seguir desarrollando **Luza Canta**: qué tecnologías usa, cómo está armada,
qué pasa con una canción desde que entra hasta que sale sin voz, cómo trabaja la IA, cuánto cuesta y
cómo podría mejorarla un ingeniero de sonido.

> App: **https://luza-canta.netlify.app** · Código: **github.com/darioriverosp/luza-canta**
> Autor: Gonzalo Dario Riveros Plaza (https://darioriverosp.netlify.app/)

---

## 1. La idea en una frase

Luza Canta es una **web app instalable (PWA)** que recibe una canción, se la manda a un **motor de IA en la nube**
que separa la voz de la música, y devuelve dos pistas (**karaoke** y **solo voz**) que en el celular se pueden
escuchar, **cambiar de tono**, mezclar con una **voz guía**, guardar y **mandar por WhatsApp**.

---

## 2. Arquitectura general

```
                ┌──────────────────────────── CELULAR / NAVEGADOR ────────────────────────────┐
                │  Luza Canta (PWA hecha con Astro: HTML + CSS + JavaScript)                   │
 WhatsApp ────► │  • Elegir canción (MP3 / link YouTube / "Compartir → Luza")                  │
 (compartir)    │  • Modo rápido (Web Audio, sin internet)                                     │
                │  • Reproductor: tono (SoundTouch), voz guía, MP3 (LAME), WhatsApp (Share API) │
                │  • Mis canciones (IndexedDB)  • Service worker (instalable, caché)           │
                └───────────────┬───────────────────────────────────────────▲─────────────────┘
                                │ 1. sube la canción / link                 │ 4. baja las 2 pistas MP3
                                ▼                                           │
   Netlify (hosting gratis) ── sirve los archivos de la web (HTML, CSS, JS, íconos)
                                │
                                ▼
                ┌──────────────────────────── MODAL (nube, Python) ───────────────────────────┐
                │  web()  → API FastAPI:  /separar  /youtube  /estado/{id}  /pista/{id}/...    │
                │      │ 2. lanza el trabajo (spawn)                                           │
                │      ▼                                                                       │
                │  procesar() → contenedor con: yt-dlp → ffprobe/ffmpeg → Demucs (IA, PyTorch) │
                │      │ 3. guarda el progreso en un Dict y devuelve los 2 MP3                 │
                └──────┴──────────────────────────────────────────────────────────────────────┘
                                ▲
   GitHub ──(Actions: "Publicar motor en Modal")── publica motor/modal_app.py en Modal
   GitHub Secrets: MODAL_TOKEN_ID, MODAL_TOKEN_SECRET, YT_COOKIES
```

Son **3 piezas**:

| Pieza | Dónde vive | Lenguaje | Qué hace |
|---|---|---|---|
| **La web app** (frontend) | Netlify | HTML, CSS, JavaScript/TypeScript con **Astro** | Todo lo que ve y toca tu mamá. Tono, voz guía, MP3, historial, WhatsApp. |
| **El motor de IA** (backend) | Modal | **Python** | Baja de YouTube, convierte el audio y separa la voz con **Demucs**. |
| **La automatización** | GitHub | YAML (GitHub Actions) | Cada cambio del motor se publica solo en Modal. |

---

## 3. Tecnologías usadas

### Frontend (en el celular)
| Tecnología | Para qué |
|---|---|
| **HTML / CSS / JavaScript** | La base de toda página web. |
| **TypeScript** (en los `<script>` de Astro) | JavaScript con tipos; ayuda a evitar errores. |
| **[Astro](https://astro.build) 7** | Arma el sitio: une el diseño (layout), las páginas y el código, y genera HTML estático optimizado. |
| **Web Audio API** (`AudioContext`, `OfflineAudioContext`) | Abrir y procesar audio dentro del navegador (modo rápido, voz guía). |
| **[SoundTouchJS](https://github.com/cutterbl/SoundTouchJS)** | Cambiar el tono sin cambiar la velocidad. Es un port a JavaScript de SoundTouch (C++). |
| **[lamejs](https://github.com/zhuker/lamejs)** (`@breezystack/lamejs`) | Crear archivos MP3 en el celular. Es un port del famoso codificador **LAME**. |
| **IndexedDB** (con `idb-keyval`) | Base de datos del navegador: "Mis canciones" se guarda en el propio celular. |
| **Service Worker + Web App Manifest** | Lo que convierte la web en **PWA** instalable. |
| **Web Share API / Web Share Target** | Enviar a WhatsApp y recibir desde WhatsApp. |
| **@fontsource** (Baloo 2, Nunito) | Fuentes servidas desde el propio sitio (más rápido que Google Fonts). |
| **sharp** (solo en desarrollo) | Genera los íconos PNG a partir del SVG. |

### Backend (motor de IA)
| Tecnología | Para qué |
|---|---|
| **Python 3.11** | Lenguaje del motor. |
| **[Modal](https://modal.com)** | Nube "serverless": corre el Python en contenedores que se prenden solo cuando hay trabajo. |
| **[FastAPI](https://fastapi.tiangolo.com)** | Crea la API web (las direcciones `/separar`, `/estado`, etc.). |
| **[Demucs](https://github.com/adefossez/demucs)** (modelo `htdemucs`) | **La IA** que separa voz e instrumentos. Creada por investigadores de Meta AI. Código abierto. |
| **[PyTorch](https://pytorch.org)** | El "motor matemático" sobre el que corre la red neuronal de Demucs. |
| **[FFmpeg / ffprobe](https://ffmpeg.org)** | Leer y convertir cualquier formato de audio. |
| **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** (+ **Deno**) | Bajar el audio de YouTube. Deno ejecuta el JavaScript que YouTube usa para proteger sus videos. |

### Infraestructura
| Servicio | Para qué | Costo |
|---|---|---|
| **GitHub** (repositorio privado) | Guarda el código y su historial. | Gratis |
| **GitHub Actions** | Publica el motor en Modal automáticamente. | Gratis (2.000 min/mes en repos privados) |
| **GitHub Secrets** | Guarda las llaves y cookies cifradas. | Gratis |
| **Netlify** | Publica la web en `luza-canta.netlify.app` con HTTPS y CDN. | Gratis |
| **Modal** | Corre la IA. | $1/mes gratis sin tarjeta, $30/mes gratis con tarjeta |

### Proyectos de código abierto de los que depende
Demucs · PyTorch · FFmpeg · yt-dlp · SoundTouch · LAME · Astro · FastAPI. Sin ellos, Luza Canta no existiría:
la app **junta** piezas de primer nivel que ya existen y les pone una interfaz pensada para un club de canto.

---

## 4. Estructura del proyecto (qué hay en cada carpeta)

```
luza-canta/
├─ src/                          ← CÓDIGO DE LA WEB (lo procesa Astro)
│  ├─ layouts/
│  │  └─ Base.astro              ← "Molde" de todas las páginas: <head>, fondo con lucecitas, logo,
│  │                               botón Instalar, menú de abajo, Ajustes y pie de página
│  ├─ pages/                     ← Cada archivo = una página (Astro usa "rutas por archivos")
│  │  ├─ index.astro             ← "/"           Pasos 1-2-3: elegir, quitar la voz, ¡a cantar!
│  │  └─ historial.astro         ← "/historial"  Mis canciones + buscador
│  ├─ scripts/                   ← La lógica en JavaScript
│  │  ├─ motor.js                ← Habla con el motor de Modal (sube, consulta estado, baja pistas)
│  │  ├─ modoRapido.js           ← Quita la voz sin IA (cancelación de fase L − R)
│  │  ├─ tono.js                 ← Sube/baja semitonos con SoundTouch
│  │  ├─ reproductor.js          ← Pantalla "¡A cantar!": pistas, voz guía, tono, guardar, WhatsApp
│  │  ├─ audio.js                ← Utilidades: decodificar, crear WAV y MP3, descargar
│  │  └─ historial.js            ← Guardar/listar/borrar canciones en IndexedDB
│  └─ styles/
│     └─ global.css              ← Todo el diseño: colores, botones, animaciones, responsive
│
├─ public/                       ← Archivos que se publican tal cual
│  ├─ manifest.webmanifest       ← "Cédula" de la PWA: nombre, ícono, colores, compartir desde WhatsApp
│  ├─ sw.js                      ← Service worker: instalación, caché, recibir lo compartido
│  └─ icons/                     ← Ícono SVG + PNG 192/512 + versión "maskable" para Android
│
├─ motor/
│  └─ modal_app.py               ← TODO EL BACKEND: imagen del contenedor, IA, YouTube y API web
│
├─ .github/workflows/
│  └─ motor.yml                  ← Receta de GitHub Actions para publicar el motor en Modal
│
├─ scripts/iconos.mjs            ← Genera los PNG de los íconos (npm run iconos)
├─ astro.config.mjs              ← Configuración de Astro (sitio estático, CSS dentro del HTML)
├─ netlify.toml / vercel.json    ← Configuración para publicar en Netlify o Vercel
├─ package.json                  ← Dependencias de JavaScript y comandos (dev, build)
├─ .env.example                  ← Ejemplo de variable PUBLIC_MOTOR_URL
└─ README.md                     ← Guía de instalación y uso
```

---

## 5. ¿Qué hace Astro y dónde se aplica?

**Astro es un generador de sitios.** Durante el desarrollo escribes componentes `.astro`; cuando ejecutas
`npm run build`, Astro produce la carpeta `dist/` con **HTML, CSS y JavaScript ya listos** para publicar.

- **Layouts** (`Base.astro`): el molde común. Las páginas lo usan con `<Base>…</Base>` y su contenido entra en `<slot />`.
- **Páginas** (`src/pages/`): `index.astro` se convierte en `/`, `historial.astro` en `/historial`.
- **Frontmatter** (lo que va entre `---` arriba del archivo): código que corre **al construir**, no en el
  celular. Ejemplo: en `Base.astro` se calculan las posiciones de las 34 lucecitas del fondo.
- **`<script>`**: el código que sí corre **en el celular**. Astro lo empaqueta y optimiza (con Vite),
  y permite importar librerías de npm como SoundTouch.
- **Estilos**: Astro mete el CSS **dentro del HTML** (`inlineStylesheets: 'always'`) para que la página se
  dibuje sin esperar otro archivo (por eso mejoró PageSpeed).

Resultado: un **sitio estático** (no necesita servidor propio). Por eso Netlify lo publica gratis.
Toda la "magia" interactiva la hace el JavaScript en el navegador y el motor en Modal.

---

## 6. ¿Es web app o PWA? ¿Cómo se instala en Android?

Es una **web app** que además cumple las reglas de **PWA (Progressive Web App)**. Una PWA es una página web que el
sistema operativo puede instalar como si fuera una app. Necesita 3 cosas:

1. **HTTPS** → Netlify lo da gratis.
2. **Manifest** (`public/manifest.webmanifest`) → nombre "Luza Canta", ícono, colores, `display: standalone`
   (se abre sin la barra del navegador) y `share_target` (aparece en "Compartir" de WhatsApp).
3. **Service worker** (`public/sw.js`) → un "ayudante" que vive en el navegador, guarda la app en caché para
   que abra rápido aunque haya mala señal, y recibe los archivos compartidos.

**En Android:** Chrome detecta esas 3 cosas y dispara el evento `beforeinstallprompt`. Luza lo atrapa y muestra
el botón amarillo **"Instalar"**. Al tocarlo, Chrome crea una **WebAPK**: un pequeño APK que Google genera
automáticamente para tu web. Por eso aparece en el cajón de apps, tiene su ícono, se abre a pantalla completa y
**aparece en el menú Compartir** como cualquier app de Play Store, pero sin pasar por Play Store.

**WhatsApp → Luza:** cuando se comparte un audio, Android lo envía a `/recibir`. El service worker lo intercepta,
lo guarda en la caché y abre `/?compartido=1`; la página lo recoge y queda listo para limpiar.

**Luza → WhatsApp:** el botón verde usa `navigator.share({ files: [mp3] })` (Web Share API), que abre el menú
nativo de Compartir de Android. Android exige que eso pase **justo después de un toque**; si preparar el MP3
tarda (por el tono), la app pide un segundo toque ("✅ Lista · toca para enviar").

---

## 7. El viaje de una canción, paso a paso

### Con IA (la opción principal)
```
 1. Elegir        Subir MP3 / pegar link / Compartir → Luza
 2. Enviar        motor.js → POST /separar (el archivo)  ó  POST /youtube (el link)
 3. En fila       web() responde al instante con un "id" y lanza procesar.spawn(...)
 4. Despertar     Si el motor dormía, Modal prende un contenedor y carga la IA (~10-20 s)
 5. YouTube*      yt-dlp baja el mejor audio disponible (con las cookies)
 6. Revisar       ffprobe mide la duración (máx. 12 min) y comprueba que sea audio
 7. Convertir     ffmpeg lo pasa a WAV estéreo 44.100 Hz (el formato que espera Demucs)
 8. Separar       Demucs (htdemucs) → vocals.mp3 + no_vocals.mp3
 9. Avisar        Cada etapa escribe un mensaje en un Dict de Modal ("Separando la voz… 🪄")
10. Consultar     El celular pregunta GET /estado/{id} cada 3 s y muestra el mensaje y los segundos
11. Bajar         GET /pista/{id}/instrumental y /voz → 2 MP3 al celular
12. Guardar       Se guardan en IndexedDB ("Mis canciones") y se abre "¡A cantar!"
13. Limpieza      El motor borra sus archivos temporales y, sin uso, se apaga a los 2 minutos
```
\* solo si fue un link.

¿Por qué "lanzar y consultar" en vez de esperar la respuesta? Porque separar una canción toma minutos y una
conexión web no debe quedar colgada tanto tiempo (el celular puede perder señal). Con un **id** el trabajo sigue
en la nube aunque se corte el internet un momento, y el celular retoma la consulta.

### Modo rápido (eliminado en la 2.6.0)
Hasta la 2.5.6 existía un modo sin IA en el celular. Se quitó por su baja calidad; ver sección 9.

---

## 8. La IA: qué es Demucs y cómo separa la voz

### Qué es
**Demucs** ("Deep Extractor for Music Sources") es una **red neuronal** creada por Alexandre Défossez y el equipo
de **Meta AI Research**. Usamos la versión **Hybrid Transformer Demucs (`htdemucs`)**, publicada en 2022-2023 en el
artículo *"Hybrid Transformers for Music Source Separation"*. Es código abierto (licencia MIT).

### Cómo aprendió (aquí sí hubo ingenieros de sonido… hace años)
La IA no "sabe" de música por reglas escritas a mano: **aprendió con ejemplos**. Se entrenó con canciones de las
que existían las **pistas separadas originales** (multipistas de estudio: la voz, la batería, el bajo y lo demás
grabados por separado), principalmente el conjunto **MUSDB18-HQ** más unos cientos de canciones adicionales.
Los ingenieros de sonido participaron **grabando y mezclando esas multipistas**. Durante el entrenamiento:

1. Se suman las pistas para crear la mezcla (como la canción final).
2. La red intenta adivinar cada pista a partir de la mezcla.
3. Se compara su adivinanza con la pista real y se corrige un poquito (millones de veces).

Al final, la red "aprendió" cómo suena una voz humana frente a una guitarra, un bajo o una batería,
incluso cuando están mezclados.

### Cómo separa (lo que pasa dentro)
El audio es una lista de números (muestras): 44.100 por segundo por canal. `htdemucs` mira la canción de **dos
formas a la vez**:

```
                        ┌─ Rama "tiempo": la onda tal cual (U-Net de convoluciones) ─┐
 mezcla (onda) ─────────┤                                                           ├─► 4 pistas
                        └─ Rama "frecuencia": espectrograma (STFT: qué notas/tonos   ┘   batería
                             suenan en cada instante)                                    bajo
                                         ▲                                               otros
                          En el medio, un Transformer (la misma familia de IA            voz
                          que los chatbots) cruza la información de ambas ramas
                          para entender el contexto musical.
```

- **Espectrograma (STFT):** convierte el sonido en una "imagen" de frecuencias en el tiempo. La voz tiene
  formas características (armónicos, vibrato, consonantes).
- **U-Net:** comprime la información para entenderla y luego la vuelve a expandir para reconstruir el sonido.
- **Transformer:** le da "memoria de contexto" (sabe qué pasó segundos antes y después).
- La canción se procesa en **trozos de ~8 segundos con solapamiento** que luego se unen sin cortes.

Demucs produce **4 pistas** (batería, bajo, otros, voz). Con la opción `--two-stems=vocals` le pedimos
**voz** y **todo lo demás sumado** (`no_vocals`) = la pista karaoke.

**Límites normales:** coros y voces de fondo pueden quedarse en la pista karaoke o en la voz; reverberación de
la voz puede dejar un "fantasma"; instrumentos muy parecidos a la voz (violín, saxo) a veces se confunden.

---

## 9. El modo rápido (sin IA): cancelación de fase — eliminado en la 2.6.0

> Se quitó de la app en la versión 2.6.0: dejaba restos de voz, perdía la batería y no servía con audios
> mono. Queda explicado aquí como referencia.

En la mayoría de canciones de estudio la **voz principal está en el centro**: suena igual en el parlante
izquierdo (L) y derecho (R). Si restas **L − R**, todo lo que es idéntico en ambos lados **se cancela**:
desaparece la voz… pero también el bajo y el bombo, que también suelen ir al centro. Por eso `modoRapido.js`:

1. Calcula `L − R` (sin voz, pero sin graves).
2. Toma el centro `(L + R) / 2`, lo filtra para dejar **solo los graves (< 140 Hz)** y lo devuelve a la mezcla.
3. Normaliza el volumen.
4. Para la "voz" aproximada filtra el centro entre 180 Hz y 6.000 Hz (rango de la voz humana).

Es instantáneo y gratis, pero de calidad sencilla: no funciona con canciones mono ni con voces con mucho eco.

---

## 10. Cómo se cambia el tono (y por qué no cambia la velocidad)

Subir **1 semitono** = multiplicar la frecuencia por **2^(1/12) ≈ 1,0595**. Si solo acelerás el audio (como un
disco a más velocidad), sube el tono **pero también la velocidad**. SoundTouch lo resuelve en dos pasos:

1. **Re-muestreo:** cambia el tono (y de paso la velocidad).
2. **Estiramiento de tiempo (WSOLA):** corta el audio en pedacitos de milisegundos y los vuelve a pegar
   superpuestos, buscando los puntos donde encajan mejor, para devolverle la **duración original**.

Todo corre en el celular (`tono.js`): por eso aparece "Cambiando el tono… 45%". En la prueba, +2 semitonos llevó
220 Hz → 247 Hz y 330 Hz → 370 Hz con la misma duración.

**Voz guía** (`reproductor.js`): es una suma simple, muestra por muestra:
`salida = pista_karaoke + voz × 0,20` (Bajita) o `× 0,35` (Media). Luego se le aplica el tono si hace falta.

**MP3:** para escuchar se usa WAV (rápido de crear); para guardar o enviar se codifica a MP3 con lamejs.

---

## 11. FFmpeg: la navaja suiza del audio

**FFmpeg** es un programa de código abierto que lee y convierte prácticamente cualquier formato de audio y video.
En el motor se usa dos veces:

- **`ffprobe`**: "radiografía" del archivo → duración. Si no puede leerlo, la app dice *"No pude leer ese archivo"*.
- **`ffmpeg -i entrada -ac 2 -ar 44100 cancion.wav`**: convierte lo que llegue (MP3, M4A, OPUS de WhatsApp,
  WEBM de YouTube…) a **WAV estéreo a 44.100 Hz**, el formato "crudo" (PCM) que Demucs necesita.

---

## 12. Cómo baja de YouTube (yt-dlp y las cookies)

**yt-dlp** se comporta como un reproductor de YouTube:
1. Pide la página del video y lee la información (título, duración, formatos disponibles).
2. YouTube protege los enlaces con un código JavaScript; yt-dlp lo resuelve con **Deno**.
3. Elige el mejor **solo-audio** (normalmente OPUS/WEBM o M4A) y lo baja.

**¿Por qué hicieron falta cookies?** YouTube bloquea las conexiones que vienen de **servidores de nube** (como
Modal), pidiendo "confirma que no eres un robot". Las **cookies** son el comprobante de una sesión iniciada en el
navegador; con ellas el motor se presenta como una persona con cuenta. Por eso:
- Se usa una **cuenta secundaria** (si YouTube la marca, no se pierde la principal).
- Las cookies **vencen**: cuando falla, se exportan de nuevo y se actualiza el secreto `YT_COOKIES`.
- Bajar contenido de YouTube va contra sus términos de servicio; Luza está pensada para uso personal del club.

---

## 13. Modal: qué es y cómo se conecta el archivo Python

**Modal** es una nube "serverless" para Python: describes **en el propio código** qué máquina necesitas y Modal
la crea, la prende cuando llega trabajo y la apaga cuando no hay. Se paga **por segundo de uso**.

En `motor/modal_app.py`:

| Código | Qué significa |
|---|---|
| `app = modal.App("luza-motor")` | El nombre de la app en Modal. |
| `modal.Image.debian_slim().apt_install("ffmpeg").pip_install("torch", "demucs", "yt-dlp", ...)` | La **imagen**: un Linux con todo instalado. Modal la construye **una vez** y la reutiliza. |
| `.run_commands("...get_model('htdemucs')")` | Baja el modelo de IA **al construir**, para no bajarlo en cada canción. |
| `@app.function(cpu=4, memory=8192, gpu=None, max_containers=1, scaledown_window=120)` | La "máquina" de `procesar`: 4 núcleos, 8 GB, una canción a la vez, se apaga a los 2 min sin uso. |
| `@modal.asgi_app(label="luza-motor")` | Publica la API FastAPI en `https://darioriverosp--luza-motor.modal.run`. |
| `procesar.spawn(...)` | Lanza el trabajo en segundo plano y devuelve un id. |
| `modal.FunctionCall.from_id(id).get(timeout=0)` | "¿Ya terminó?" sin esperar. |
| `modal.Dict.from_name("luza-progreso")` | Diccionario compartido para los mensajes de progreso. |
| `modal.Secret.from_name("luza-youtube")` | Mete las cookies como variable de entorno, sin estar en el código. |

Son **dos funciones** con imágenes distintas: `web` (liviana, siempre lista para responder) y `procesar`
(pesada, con la IA, solo se prende cuando hay canción).

---

## 14. GitHub Actions y los Secrets

**`.github/workflows/motor.yml`** es una "receta" que GitHub ejecuta en una máquina temporal cada vez que cambia
algo en `motor/` (o al tocar **Run workflow**):

1. Descarga el código del repositorio.
2. Instala Python y la herramienta `modal`.
3. Copia las cookies de YouTube (secreto `YT_COOKIES`) a un secreto de Modal (`luza-youtube`).
4. Ejecuta `modal deploy motor/modal_app.py` → Modal construye la imagen y publica el motor.

Gracias a esto **no hizo falta instalar Python en la PC**: todo se construye en la nube.

**¿Por qué las llaves van en Secrets?**
- `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` son el "usuario y contraseña" de la herramienta `modal` para entrar a
  **tu cuenta de Modal** y publicar. Con ellas cualquiera podría usar tus créditos.
- `YT_COOKIES` da acceso a la cuenta de Google secundaria.

Los **GitHub Secrets** se guardan **cifrados**, no se ven en el código ni en los registros (aparecen como `***`)
y solo los usa el workflow. **Nunca** se deben pegar en el código, en un chat ni en capturas.

---

## 15. Tiempos: ¿por qué tarda lo que tarda?

| Etapa | Tiempo aproximado |
|---|---|
| Subir la canción (4-8 MB) | 2-10 s según la señal |
| Despertar el motor si dormía (prender contenedor + cargar la IA en memoria) | 10-20 s |
| Bajar de YouTube (si es link) | 3-10 s |
| ffmpeg (convertir) | 1-3 s |
| **Demucs separando** (la parte pesada) | **la mayor parte del tiempo** |
| Bajar las 2 pistas MP3 al celular | 2-10 s |

Medido en pruebas: un audio de 10 segundos tardó **19-27 s** en total (incluyendo despertar).
Para una canción de 3-4 minutos en **CPU**, calcula del orden de **2 a 4 minutos**.

**¿Por qué la IA tarda?** Para cada trozo de ~8 s, la red hace **miles de millones de multiplicaciones**.
Una **CPU** tiene pocos núcleos (aquí 4) que hacen esas cuentas casi una por una; una **GPU** tiene miles de
núcleos pequeños que hacen muchas a la vez.

---

## 16. CPU vs GPU: por qué CPU y cuándo migrar

- **Por qué CPU:** Modal **pide una tarjeta registrada para usar GPU**, aunque no cobre más allá de los créditos.
  Sin tarjeta, solo CPU. Así Luza funciona hoy **sin tarjeta**.
- **Con GPU (T4):** la separación pasa de minutos a **segundos** (del orden de 5-10 veces más rápido).
  El costo por canción es parecido, porque aunque la GPU cuesta más por segundo, usa muchos menos segundos.
- **Cómo migrar:** agregar la tarjeta en Modal → en GitHub: *Settings → Secrets and variables → Actions →
  Variables* → `MOTOR_GPU = T4` → *Actions → Publicar motor en Modal → Run workflow*. El código ya está listo
  (`gpu=GPU` en `modal_app.py`).
- **¿Conviene?** Sí, si el club la usa seguido: la espera de 2-4 minutos baja a menos de 1 minuto y con tarjeta
  hay **$30 al mes gratis**.

---

## 17. Costos y créditos

| Servicio | Costo para Luza |
|---|---|
| Netlify (web) | $0 (plan gratis) |
| GitHub (código + Actions + Secrets) | $0 |
| Fuentes, librerías, Demucs, FFmpeg, yt-dlp | $0 (código abierto) |
| **Modal (IA)** | Se paga por segundo de CPU/GPU y memoria **solo mientras procesa**. Dormido = $0. |

- **Créditos de Modal:** $1/mes gratis sin tarjeta; **$30/mes gratis** con tarjeta (se renuevan cada mes, no se acumulan).
- **Estimación:** del orden de **1 centavo de dólar por canción** en CPU → $1 ≈ 70-100 canciones/mes;
  $30 ≈ varios miles. (Valores aproximados: revisa *Usage & billing* en Modal para el consumo real.)
- **Protecciones:** `max_containers=1` (una canción a la vez), apagado automático a los 2 min, límite de 12 min
  por canción y 60 MB por archivo. Recomendado: poner un **límite de gasto** en Modal.

---

## 18. Entorno de desarrollo

| Herramienta | Uso |
|---|---|
| Windows 11 + **VS Code / Claude Code** | Escribir y revisar el código con ayuda de IA. |
| **Node.js 24 + npm** | Instalar dependencias y correr Astro. |
| `npm run dev` | Servidor local en `http://localhost:4321` con recarga automática. |
| `npm run build` | Genera `dist/` (lo que se publica). |
| **git + GitHub CLI (`gh`)** | Versionar y subir el código, crear el repo, ver los workflows. |
| **Netlify CLI** (`npx netlify-cli deploy --prod --dir dist`) | Publicar la web. |
| **Modal** | Construye y corre el motor en la nube (no hace falta Python local). |
| **PageSpeed Insights** | Medir rendimiento (91 → optimizado: CSS en el HTML, fuentes propias, caché de 1 año). |

---

## 19. Cómo lo entiende un programador (y qué aporta un ingeniero de sonido)

### Conceptos de audio que conviene dominar
- **Muestra / sample rate:** el sonido digital es una lista de números; 44.100 por segundo (calidad CD).
- **Canales:** mono (1) o estéreo (2: L y R).
- **PCM / WAV:** audio "crudo" sin comprimir. **MP3/OPUS/M4A:** comprimidos.
- **Frecuencia y semitonos:** La4 = 440 Hz; cada semitono multiplica por 1,0595; una octava = ×2.
- **Fase:** dos ondas iguales e invertidas se cancelan (base del modo rápido).
- **Espectrograma / STFT:** el sonido visto como frecuencias en el tiempo (como "ve" el audio la IA).
- **dB y LUFS:** volumen relativo y volumen percibido (normalización).

Como programador, Luza es un **pipeline**: entrada → conversión → modelo → salida → post-proceso en el cliente.
Cada etapa se puede probar por separado (como hicimos: medir 440 Hz antes/después para verificar que la voz se fue).

### Qué haría un ingeniero de sonido en el equipo
1. **Escuchar y evaluar la calidad** con canciones reales del club: voces "fantasma", coros perdidos, sonido "acuoso".
2. **Elegir mejores modelos:** `htdemucs_ft` (afinado, mejor y más lento) o modelos de la familia **RoFormer**
   (BS-RoFormer, Mel-Band RoFormer), hoy de los mejores para separar voces; o combinar varios ("ensemble").
3. **Post-producción automática:** normalizar volumen (p. ej. −14 LUFS), ecualizar, quitar reverberación residual.
4. **Opción de dejar los coros** en la pista karaoke (algunos modelos separan voz principal y coros).
5. **Mejor cambio de tono:** librerías como **Rubber Band** preservan los **formantes** (el timbre) y suenan
   más naturales en cambios grandes.
6. **Grabación:** si se agrega "grabarse cantando", manejar latencia, eco y mezcla voz + pista.
7. **Crear un set de pruebas:** 10-20 canciones típicas del club para comparar cada mejora con números (SDR) y oídos.

**Reparto natural:** el programador construye la app, la nube y la automatización; el ingeniero de sonido define
**qué suena bien**, elige y ajusta los modelos y la cadena de procesamiento.

---

## 20. Guion sugerido para el video

1. **El problema** (30 s): el club baja canciones y les quita la voz a mano.
2. **Demo** (1-2 min): compartir desde WhatsApp → quitar la voz → voz guía → tono → enviar por WhatsApp.
3. **Arquitectura** (1 min): diagrama de la sección 2 — celular, Netlify, Modal, GitHub.
4. **Frontend** (1-2 min): Astro, estructura de carpetas, PWA e instalación en Android.
5. **La IA** (2 min): qué es Demucs, cómo aprendió, espectrograma + Transformer, 4 pistas → 2.
6. **El audio en el celular** (1 min): cancelación de fase, semitonos, voz guía, MP3.
7. **La nube** (1-2 min): Modal, `modal_app.py`, spawn + estado, FFmpeg, yt-dlp y cookies.
8. **Automatización y seguridad** (1 min): GitHub Actions y Secrets.
9. **Costos y rendimiento** (1 min): todo gratis salvo Modal (~1 ¢/canción), CPU vs GPU, PageSpeed.
10. **Próximos pasos** (30 s): GPU, mejores modelos, grabarse cantando, ingeniero de sonido.
