// Network sign-up: the site's "Join the network" form POSTs here and the person is added
// to public.network_signups in Supabase (private table; see build/network_signups_schema.sql).
// Web-standard handler on Vercel's Edge runtime, global fetch only (no deps), same pattern
// as paypal-ipn.js.
//
// Required env (server-side only; already set for the donation functions):
//   SUPABASE_SERVICE_ROLE_KEY
// Optional env:
//   SUPABASE_URL   defaults to the project URL below

export const config = { runtime: 'edge' };

const SB_URL = process.env.SUPABASE_URL || 'https://aykhwsermojstiyrfcnv.supabase.co';
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
const LISTS = new Set(['mailing', 'action']);
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

// Only our own pages may post (production, Vercel previews, local testing).
function originOk(o) {
  if (!o) return true; // same-origin form posts from some browsers omit Origin
  try {
    const h = new URL(o).hostname;
    return h === 'spraymapca.org' || h.endsWith('.spraymapca.org') || h.endsWith('.vercel.app') || h === 'localhost';
  } catch (e) { return false; }
}

const json = (obj, status) => new Response(JSON.stringify(obj), {
  status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
});

export default async function handler(request) {
  if (request.method !== 'POST') return json({ ok: false, error: 'POST only' }, 405);
  if (!originOk(request.headers.get('origin'))) return json({ ok: false, error: 'origin' }, 403);

  let b;
  try { b = await request.json(); } catch (e) { return json({ ok: false, error: 'bad json' }, 400); }
  // Honeypot: a hidden field real people never fill. Pretend success so bots move on.
  if (b && b.website) return json({ ok: true, status: 'added' }, 200);

  const email = String((b && b.email) || '').trim().toLowerCase().slice(0, 254);
  const name = String((b && b.name) || '').trim().slice(0, 120);
  const lists = Array.isArray(b && b.lists) ? [...new Set(b.lists.filter((l) => LISTS.has(l)))] : [];
  if (!name || !EMAIL_RE.test(email)) return json({ ok: false, error: 'name and a valid email are required' }, 400);
  if (!SERVICE_KEY) return json({ ok: false, error: 'server not configured' }, 500);

  const r = await fetch(SB_URL + '/rest/v1/rpc/network_signup', {
    method: 'POST',
    headers: { apikey: SERVICE_KEY, Authorization: 'Bearer ' + SERVICE_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ p_email: email, p_name: name, p_lists: lists.length ? lists : ['mailing'], p_source: 'site', p_note: null }),
  });
  if (!r.ok) {
    const t = await r.text().catch(() => '');
    return json({ ok: false, error: 'store failed: ' + r.status + ' ' + t.slice(0, 160) }, 502);
  }
  const status = await r.json().catch(() => 'added'); // 'added' | 'updated' | 'unsubscribed'
  return json({ ok: true, status }, 200);
}
