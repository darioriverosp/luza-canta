// "Compartir → Luza" cuando el service worker todavía no está listo (recién instalada o actualizada):
// el envío llega aquí en vez de a public/sw.js. Se saca el link y se abre la portada con él.
// (Un audio de WhatsApp no se puede guardar aquí: en ese caso solo se abre la portada.)
export default async (req) => {
  if (req.method !== 'POST') return; // las visitas normales siguen a la regla de netlify.toml
  let texto = '';
  try {
    const datos = await req.formData();
    texto = `${datos.get('url') || ''} ${datos.get('text') || ''}`;
  } catch {}
  const link = texto.match(/https?:\/\/\S+/);
  return Response.redirect(new URL(link ? `/?link=${encodeURIComponent(link[0])}` : '/', req.url), 303);
};

export const config = { path: '/recibir' };
