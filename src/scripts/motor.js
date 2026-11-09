// Conexión con el "motor" de Luza Canta (el de tu PC por túnel, o el de Modal): quita la voz con Demucs + yt-dlp.
const CLAVE = 'luza-motor';
const POR_DEFECTO = 'https://darioriverosp--luza-motor.modal.run';

export function motorConfigurado() {
  return obtenerMotor() !== '';
}

export function obtenerMotor() {
  let guardado = '';
  try {
    guardado = localStorage.getItem(CLAVE) || '';
  } catch {}
  return (guardado || import.meta.env.PUBLIC_MOTOR_URL || POR_DEFECTO).trim().replace(/\/+$/, '');
}

export function guardarMotor(valor) {
  try {
    if (valor.trim()) localStorage.setItem(CLAVE, valor.trim());
    else localStorage.removeItem(CLAVE);
  } catch {}
}

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

class ErrorConexion extends Error {
  constructor() {
    super('No hay conexión con el motor. Revisa el internet e intenta de nuevo.');
    this.esConexion = true;
  }
}

// ngrok pone una página de aviso por delante de las peticiones del navegador;
// este encabezado se la salta. Los otros motores (Modal, cloudflared) lo ignoran.
const ENCABEZADOS = () => ({ 'ngrok-skip-browser-warning': 'luza' });

async function pedir(base, ruta, opciones) {
  let r;
  try {
    r = await fetch(`${base}${ruta}`, { ...opciones, headers: { ...ENCABEZADOS(), ...(opciones?.headers || {}) } });
  } catch {
    throw new ErrorConexion();
  }
  if (!r.ok) {
    let detalle = '';
    try {
      detalle = (await r.json()).detail;
    } catch {}
    throw new Error(typeof detalle === 'string' && detalle ? detalle : `El motor respondió con un error (${r.status}).`);
  }
  return r;
}

/**
 * Le pide a un motor (el configurado) y, si no hay manera de conectarse, intenta
 * igual con el de Modal de respaldo. Devuelve { base, r }: hay que seguir
 * preguntándole a ESE motor (el trabajo quedó en su memoria).
 */
async function pedirConRespaldo(ruta, opciones) {
  const motores = [];
  for (const m of [obtenerMotor(), POR_DEFECTO]) {
    const base = m.trim().replace(/\/+$/, '');
    if (base && !motores.includes(base)) motores.push(base);
  }
  let ultimo;
  for (const base of motores) {
    try {
      return { base, r: await pedir(base, ruta, opciones) };
    } catch (e) {
      if (e?.esConexion) {
        ultimo = e;
        continue;
      }
      throw e; // el motor contestó (con un aviso útil): no se reintenta en otro
    }
  }
  throw ultimo || new Error('No hay conexión con el motor.');
}

// Baja una pista ya lista. Si se corta a medio bajar (señal del celular, pantalla apagada), el
// navegador da un "Failed to fetch" pelado: se reintenta, la pista sigue guardada en el motor.
async function bajarPista(base, id, cual) {
  for (let intento = 1; ; intento++) {
    try {
      return await (await pedir(base, `/pista/${encodeURIComponent(id)}/${cual}`)).blob();
    } catch (e) {
      if (e?.esConexion === undefined && !(e instanceof TypeError)) throw e; // el motor contestó con un aviso
      if (intento >= 4) throw new Error('Se cortó el internet mientras bajaban las pistas. Revisa la señal y toca de nuevo “Quitar la voz con IA”.');
      await esperar(3000 * intento);
    }
  }
}

/**
 * Envía la canción al motor.
 * entrada = { archivo: File } o { youtube: 'https://...' }
 * Devuelve { titulo, instrumental: Blob, voz: Blob }
 */
export async function separarConIA(entrada, aviso) {
  aviso('Enviando la canción… 📤');
  let elegido;
  if (entrada.archivo) {
    const datos = new FormData();
    datos.append('archivo', entrada.archivo);
    elegido = await pedirConRespaldo('/separar', { method: 'POST', body: datos });
  } else {
    elegido = await pedirConRespaldo('/youtube', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ link: entrada.youtube }),
    });
  }
  const { base } = elegido;
  let id;
  try {
    ({ id } = await elegido.r.json());
  } catch {
    throw new ErrorConexion(); // se cortó justo al recibir la respuesta
  }

  const inicio = Date.now();
  let estado;
  while (true) {
    await esperar(3000);
    try {
      estado = await (await pedir(base, `/estado/${encodeURIComponent(id)}`)).json();
    } catch (e) {
      if (Date.now() - inicio > 15 * 60 * 1000) throw e;
      continue; // un corte de señal momentáneo no detiene el trabajo
    }
    if (estado.error) throw new Error(estado.error);
    if (estado.listo) break;
    const seg = Math.round((Date.now() - inicio) / 1000);
    aviso(`${estado.mensaje || 'Trabajando…'}  ·  ${seg} s`);
    if (Date.now() - inicio > 15 * 60 * 1000) throw new Error('El motor está tardando demasiado. Intenta de nuevo más tarde.');
  }

  aviso('Bajando las pistas al celular… 📲');
  const [inst, voz] = await Promise.all([
    bajarPista(base, id, 'instrumental'),
    bajarPista(base, id, 'voz'),
  ]);
  return {
    titulo: estado.titulo || entrada.archivo?.name?.replace(/\.[^.]+$/, '') || 'Canción',
    instrumental: inst,
    voz,
  };
}
