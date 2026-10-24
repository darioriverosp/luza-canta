"""Motor de Luza Canta en Modal: quita la voz de una canción con Demucs (IA de código abierto).

Se publica solo desde GitHub (ver .github/workflows/motor.yml). Queda en:
    https://<tu-usuario-de-modal>--luza-motor.modal.run

API que usa la web:
    POST /separar          (formulario con "archivo")  -> {"id": ...}
    POST /youtube          {"link": "https://..."}     -> {"id": ...}
    GET  /estado/{id}                                   -> {"listo": bool, "mensaje": str, "titulo": str, "error": str}
    GET  /pista/{id}/{instrumental|voz}                 -> MP3
"""

import os

import modal

# Sin tarjeta en Modal se usa CPU (2–4 min por canción). Con tarjeta, poner la variable MOTOR_GPU=T4
# en GitHub (Settings → Secrets and variables → Actions → Variables) para que tarde menos de 1 minuto.
GPU = os.environ.get("MOTOR_GPU") or None
MAX_MINUTOS = 12
MODELO = "htdemucs"

app = modal.App("luza-motor")

imagen_ia = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install("torch", "numpy", "demucs==4.1.0", "yt-dlp[default]", "deno")
    # Baja el modelo de IA al construir la imagen, así no se descarga en cada canción
    .run_commands(f"python -c \"from demucs.pretrained import get_model; get_model('{MODELO}')\"")
)
imagen_web = modal.Image.debian_slim(python_version="3.11").pip_install("fastapi[standard]", "python-multipart")

# Mensajes de progreso que la web va mostrando ("Bajando de YouTube…", "Separando la voz…")
progreso = modal.Dict.from_name("luza-progreso", create_if_missing=True)


class ErrorAmable(Exception):
    """Error con un mensaje pensado para mostrárselo a la usuaria tal cual.

    Puede llevar al final un detalle técnico tras DETALLE: /estado lo separa y lo devuelve aparte para diagnosticar.
    (Va en el mismo texto porque Modal, al pasar el error entre contenedores, solo conserva bien un mensaje.)
    """


DETALLE = "\n[detalle] "


@app.function(
    image=imagen_ia,
    gpu=GPU,
    cpu=4.0,
    memory=8192,
    timeout=15 * 60,
    max_containers=1,  # una canción a la vez: limita el gasto
    scaledown_window=120,  # se apaga a los 2 minutos sin uso (no cobra mientras duerme)
    secrets=[modal.Secret.from_name("luza-youtube")],  # cookies de YouTube (las crea el workflow de GitHub)
)
def procesar(origen: dict) -> dict:
    import shutil
    import tempfile
    from pathlib import Path

    id_trabajo = modal.current_function_call_id()

    def avisar(texto):
        progreso[id_trabajo] = texto

    trabajo = Path(tempfile.mkdtemp())
    try:
        return _procesar(origen, trabajo, avisar)
    finally:
        # Borra los archivos de esta canción para no llenar el disco del contenedor
        shutil.rmtree(trabajo, ignore_errors=True)


_ytdlp_al_dia = False


def _actualizar_ytdlp():
    """YouTube cambia seguido y un yt-dlp viejo deja de bajar: se pone al día una vez por contenedor.

    La imagen guarda la versión del día en que se construyó, así que sin esto se quedaría vieja para siempre.
    Se usa la versión "nightly" (--pre), que es la que yt-dlp recomienda para YouTube.
    """
    global _ytdlp_al_dia
    if _ytdlp_al_dia:
        return
    import subprocess
    import sys

    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-U", "--pre", "yt-dlp[default]"],
        capture_output=True, text=True, timeout=120,
    )
    print(f"yt-dlp: actualización {'ok' if r.returncode == 0 else 'falló: ' + r.stderr[-500:]}", flush=True)
    _ytdlp_al_dia = True  # aunque falle, no se reintenta en cada canción: se usa la versión de la imagen


def _clave_rapidapi() -> str:
    clave = os.environ.get("RAPIDAPI_KEY", "").strip()
    return "" if clave in ("", "ninguna") else clave


def _bajar_con_rapidapi(link: str, trabajo):
    """Pide el MP3 al servicio "YouTube MP3" de RapidAPI (youtube-mp36), que baja desde sus propios servidores.

    YouTube bloquea a Modal por ser un servidor en la nube; este servicio no tiene ese problema.
    Plan gratis: 300 canciones al mes. Clave: secreto RAPIDAPI_KEY en GitHub.
    Devuelve (archivo, título). Si algo falla lanza Exception y se intenta igual con yt-dlp.
    """
    import json
    import re
    import time
    import urllib.parse
    import urllib.request

    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})", link)
    if not m:
        raise Exception("no encontré el id del video en el link")
    anfitrion = "youtube-mp36.p.rapidapi.com"
    pedido = urllib.request.Request(
        f"https://{anfitrion}/dl?id={m.group(1)}",
        headers={"x-rapidapi-key": _clave_rapidapi(), "x-rapidapi-host": anfitrion},
    )
    # Si la canción es nueva para el servicio, contesta "processing" unos segundos: se vuelve a preguntar
    for _ in range(12):
        with urllib.request.urlopen(pedido, timeout=60) as r:
            datos = json.loads(r.read())
        if datos.get("status") != "processing":
            break
        time.sleep(5)
    if datos.get("status") != "ok" or not datos.get("link"):
        raise Exception(f"respuesta: {json.dumps(datos, ensure_ascii=False)[:200]}")
    if float(datos.get("duration") or 0) > MAX_MINUTOS * 60:
        raise ErrorAmable(f"La canción dura más de {MAX_MINUTOS} minutos. Elige una más corta.")

    archivo = trabajo / "descarga.mp3"
    # El servidor del MP3 responde 404 si la petición no parece de un navegador que viene de RapidAPI
    bajada = urllib.request.Request(datos["link"], headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/130.0 Safari/537.36",
        "Referer": "https://rapidapi.com/",
    })
    with urllib.request.urlopen(bajada, timeout=120) as r, open(archivo, "wb") as f:
        total = 0
        while bloque := r.read(1 << 16):
            total += len(bloque)
            if total > 60 * 1024 * 1024:
                raise ErrorAmable("La canción es muy pesada (más de 60 MB). Elige una más corta.")
            f.write(bloque)
    if total < 10_000:
        raise Exception(f"el MP3 bajado está vacío ({total} bytes)")
    print(f"RapidAPI: bajó {total // 1024} KB", flush=True)
    return archivo, datos.get("title") or "Canción"


def _procesar(origen: dict, trabajo, avisar) -> dict:
    import json
    import os
    import re
    import subprocess

    titulo = origen.get("titulo") or "Canción"

    original = None
    fallos = []
    if origen.get("link") and _clave_rapidapi():
        avisar("Bajando la canción de YouTube… ▶️")
        try:
            original, titulo = _bajar_con_rapidapi(origen["link"], trabajo)
        except ErrorAmable:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"RapidAPI: {e}", flush=True)
            fallos.append(f"[rapidapi] {str(e)[:200]}")

    if origen.get("link") and original is None:
        avisar("Preparando la descarga de YouTube… ▶️")
        _actualizar_ytdlp()
        import yt_dlp

        print(f"yt-dlp {yt_dlp.version.__version__}", flush=True)
        avisar("Bajando la canción de YouTube… ▶️")
        opciones = {
            "format": "bestaudio/best",
            "outtmpl": str(trabajo / "descarga.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "max_filesize": 60 * 1024 * 1024,
            "match_filter": yt_dlp.utils.match_filter_func(f"duration <= {MAX_MINUTOS * 60}"),
        }
        # YouTube pide "demostrar que no eres un robot" a los servidores en la nube. Se prueban, en orden:
        # las cookies (secreto YT_COOKIES en GitHub, si hay) y luego, sin cookies, otros reproductores de
        # YouTube (tele, Safari, móvil…) que a veces piden menos verificación. Gana el primero que baje.
        intentos = []
        if "youtube.com" in os.environ.get("YT_COOKIES", ""):
            (trabajo / "cookies.txt").write_text(os.environ["YT_COOKIES"])
            intentos.append(("cookies", {"cookiefile": str(trabajo / "cookies.txt")}))
        intentos.append(("normal", {}))
        for cliente in ["tv_simply", "tv", "web_safari", "mweb", "android_vr", "web_embedded"]:
            intentos.append((cliente, {"extractor_args": {"youtube": {"player_client": [cliente]}}}))

        info = None
        for nombre, extra in intentos:
            for viejo in trabajo.glob("descarga.*"):
                viejo.unlink()
            try:
                with yt_dlp.YoutubeDL({**opciones, **extra}) as ydl:
                    info = ydl.extract_info(origen["link"], download=True)
                print(f"yt-dlp: bajó con '{nombre}'", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print(f"yt-dlp [{nombre}]: {e}", flush=True)
                fallos.append(f"[{nombre}] {str(e)[:160]}")
        else:
            raise ErrorAmable(
                "YouTube no dejó bajar esta canción 😕. Descárgala aparte y usa “Subir MP3”."
                f"{DETALLE}yt-dlp {yt_dlp.version.__version__}: " + " | ".join(fallos)
            )
        archivos = list(trabajo.glob("descarga.*"))
        if not info or not archivos:
            raise ErrorAmable(f"No se pudo bajar. ¿La canción dura más de {MAX_MINUTOS} minutos?")
        original = archivos[0]
        titulo = info.get("title") or titulo
    elif original is None:
        original = trabajo / "subida"
        original.write_bytes(origen["audio"])

    sonda = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(original)],
        capture_output=True, text=True,
    )
    try:
        duracion = float(json.loads(sonda.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        raise ErrorAmable("No pude leer ese archivo. ¿Seguro que es una canción (MP3, M4A, WAV)?")
    if duracion > MAX_MINUTOS * 60:
        raise ErrorAmable(f"La canción dura más de {MAX_MINUTOS} minutos. Elige una más corta.")

    avisar("Preparando la canción… 🎼")
    entrada = trabajo / "cancion.wav"
    conversion = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(original), "-ac", "2", "-ar", "44100", str(entrada)],
        capture_output=True, text=True,
    )
    if conversion.returncode != 0:
        print(conversion.stderr[-3000:], flush=True)
        raise ErrorAmable("No pude leer ese archivo. ¿Seguro que es una canción (MP3, M4A, WAV)?")

    avisar("La inteligencia artificial está separando la voz… 🪄")
    r = subprocess.run(
        ["python", "-m", "demucs", "-n", MODELO, "--two-stems=vocals", "--mp3", "--mp3-bitrate", "192",
         "-o", str(trabajo / "salida"), str(entrada)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(r.stderr[-3000:], flush=True)
        raise ErrorAmable("La IA no pudo procesar esta canción. Intenta con otro archivo.")

    carpeta = trabajo / "salida" / MODELO / "cancion"
    avisar("¡Listo! 🎉")
    return {
        "titulo": re.sub(r"\s+", " ", titulo).strip()[:120],
        "instrumental": (carpeta / "no_vocals.mp3").read_bytes(),
        "voz": (carpeta / "vocals.mp3").read_bytes(),
    }


@app.function(image=imagen_web, max_containers=2)
@modal.concurrent(max_inputs=20)
@modal.asgi_app(label="luza-motor")
def web():
    import re

    from fastapi import FastAPI, File, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import Response
    from pydantic import BaseModel

    api = FastAPI(title="Luza Motor")
    api.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    youtube = re.compile(r"^(https?://)?(www\.|m\.|music\.)?(youtube\.com|youtu\.be)/", re.I)

    class Link(BaseModel):
        link: str

    def resultado(id_: str):
        """Devuelve el resultado si ya terminó, o None si sigue trabajando."""
        llamada = modal.FunctionCall.from_id(id_)
        try:
            return llamada.get(timeout=0)
        except (TimeoutError, modal.exception.TimeoutError):
            return None

    @api.get("/")
    def hola():
        return {"motor": "Luza Canta", "ok": True}

    @api.post("/separar")
    async def separar(archivo: UploadFile = File(...)):
        datos = await archivo.read()
        if not datos:
            raise HTTPException(400, "El archivo está vacío.")
        if len(datos) > 60 * 1024 * 1024:
            raise HTTPException(413, "El archivo es muy grande (máximo 60 MB).")
        titulo = re.sub(r"\.[^.]+$", "", archivo.filename or "Canción")
        llamada = procesar.spawn({"audio": datos, "titulo": titulo})
        return {"id": llamada.object_id}

    @api.post("/youtube")
    def desde_youtube(cuerpo: Link):
        if not youtube.match(cuerpo.link.strip()):
            raise HTTPException(400, "Ese no parece un link de YouTube.")
        llamada = procesar.spawn({"link": cuerpo.link.strip()})
        return {"id": llamada.object_id}

    @api.get("/estado/{id_}")
    def estado(id_: str):
        try:
            r = resultado(id_)
        except ErrorAmable as e:
            error, _, detalle = str(e).partition(DETALLE)
            return {"listo": False, "error": error, "detalle": detalle}
        except Exception as e:  # noqa: BLE001
            print(f"estado {id_}: {e!r}", flush=True)
            return {"listo": False, "error": "Algo salió mal con el motor. Intenta de nuevo."}
        if r is None:
            return {"listo": False, "mensaje": progreso.get(id_, "Despertando la inteligencia artificial o esperando turno… ⏳ (puede tardar 1 o 2 minutos)")}
        return {"listo": True, "titulo": r["titulo"]}

    @api.get("/pista/{id_}/{cual}")
    def pista(id_: str, cual: str):
        if cual not in ("instrumental", "voz"):
            raise HTTPException(404)
        try:
            r = resultado(id_)
        except Exception:  # noqa: BLE001  (la canción falló: no hay pista que devolver)
            raise HTTPException(404, "Esta canción no se pudo procesar.")
        if r is None:
            raise HTTPException(409, "Todavía no está lista.")
        return Response(r[cual], media_type="audio/mpeg")

    return api
