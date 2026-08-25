// Daily reconciliation safety net (Vercel Cron -> GET).
// Always: recompute donation_totals = baseline + sum(Completed events).
// If PayPal REST creds are present: also backfill any events that never arrived
// via IPN (e.g. a webhook outage) by scanning the last ~31 days of transactions,
// then recompute. Backfill is best-effort and never blocks the recompute.
//
// Must use a Web fetch handler / named HTTP method export. A default
// (req, res) function that returns `new Response()` is ignored and the
// cron then times out at 300s.
//
// Required env:
//   SUPABASE_SERVICE_ROLE_KEY
// Optional env:
//   SUPABASE_URL
//   CRON_SECRET            if set, requests must send Authorization: Bearer <it>
//                          (Vercel Cron sends this automatically when the env var exists)
//   PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET   enable the PayPal backfill
//   PAYPAL_API_BASE       defaults to live; set sandbox base to test

const SB_URL = process.env.SUPABASE_URL || 'https://aykhwsermojstiyrfcnv.supabase.co';
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
const CRON_SECRET = process.env.CRON_SECRET || '';
const PP_BASE = process.env.PAYPAL_API_BASE || 'https://api-m.paypal.com';
const PP_ID = process.env.PAYPAL_CLIENT_ID || '';
const PP_SECRET = process.env.PAYPAL_CLIENT_SECRET || '';

const NAME_EFFORT = [
  ['spraymap', 'SprayMap California'],
  ['water', 'Water testing'],
  ['goat', 'Goat grazing'],
];
function effortFromName(nm) {
  const s = (nm || '').toLowerCase();
  for (const [needle, eff] of NAME_EFFORT) if (s.includes(needle)) return eff;
  return 'Unallocated';
}

function timeoutSignal(ms) {
  if (typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function') {
    return AbortSignal.timeout(ms);
  }
  const c = new AbortController();
  setTimeout(() => c.abort(), ms);
  return c.signal;
}

function headerGet(request, name) {
  const h = request && request.headers;
  if (!h) return '';
  if (typeof h.get === 'function') return h.get(name) || '';
  return h[name] || h[name.toLowerCase()] || '';
}

export const config = { maxDuration: 30 };

async function ppToken() {
  const auth = Buffer.from(PP_ID + ':' + PP_SECRET).toString('base64');
  const r = await fetch(PP_BASE + '/v1/oauth2/token', {
    method: 'POST',
    headers: { Authorization: 'Basic ' + auth, 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'grant_type=client_credentials',
    signal: timeoutSignal(15000),
  });
  if (!r.ok) throw new Error('paypal token ' + r.status);
  return (await r.json()).access_token;
}

async function backfillFromPayPal() {
  const token = await ppToken();
  const end = new Date();
  const start = new Date(end.getTime() - 31 * 24 * 3600 * 1000);
  const qs = new URLSearchParams({
    start_date: start.toISOString().replace(/\.\d+Z$/, 'Z'),
    end_date: end.toISOString().replace(/\.\d+Z$/, 'Z'),
    fields: 'all',
    page_size: '100',
  });
  const r = await fetch(PP_BASE + '/v1/reporting/transactions?' + qs.toString(), {
    headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
    signal: timeoutSignal(20000),
  });
  if (!r.ok) throw new Error('transaction search ' + r.status);
  const data = await r.json();
  const txns = data.transaction_details || [];
  const rows = [];
  for (const t of txns) {
    const info = t.transaction_info || {};
    if (info.transaction_status !== 'S') continue;
    const items = (t.cart_info && t.cart_info.item_details) || [];
    const itemName = items.length ? items[0].item_name : '';
    const gross = parseFloat((info.transaction_amount && info.transaction_amount.value) || '0') || 0;
    const fee = Math.abs(parseFloat((info.fee_amount && info.fee_amount.value) || '0') || 0);
    rows.push({
      txn_id: info.transaction_id,
      effort: effortFromName(itemName),
      button_id: null,
      item_name: itemName || null,
      gross,
      fee,
      net: +(gross - fee).toFixed(2),
      currency: (info.transaction_amount && info.transaction_amount.currency_code) || 'USD',
      status: 'Completed',
      source: 'reconcile',
      raw: t,
    });
  }
  if (!rows.length) return 0;
  const up = await fetch(SB_URL + '/rest/v1/donation_events', {
    method: 'POST',
    headers: {
      apikey: SERVICE_KEY,
      Authorization: 'Bearer ' + SERVICE_KEY,
      'Content-Type': 'application/json',
      Prefer: 'resolution=ignore-duplicates',
    },
    body: JSON.stringify(rows),
    signal: timeoutSignal(10000),
  });
  if (!up.ok) throw new Error('event upsert ' + up.status);
  return rows.length;
}

async function recompute() {
  const r = await fetch(SB_URL + '/rest/v1/rpc/recompute_donation_totals', {
    method: 'POST',
    headers: { apikey: SERVICE_KEY, Authorization: 'Bearer ' + SERVICE_KEY, 'Content-Type': 'application/json' },
    body: '{}',
    signal: timeoutSignal(10000),
  });
  if (!r.ok) throw new Error('recompute ' + r.status);
}

async function handle(request) {
  if (CRON_SECRET) {
    const auth = headerGet(request, 'authorization');
    if (auth !== 'Bearer ' + CRON_SECRET) return new Response('Unauthorized', { status: 401 });
  }
  if (!SERVICE_KEY) return new Response('server not configured', { status: 500 });

  let scanned = 0, ppError = null;
  if (PP_ID && PP_SECRET) {
    try { scanned = await backfillFromPayPal(); }
    catch (e) { ppError = String(e && e.message || e); }
  }
  await recompute();

  return new Response(JSON.stringify({ ok: true, backfill_scanned: scanned, paypal: PP_ID ? (ppError || 'ok') : 'disabled' }), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  });
}

export function GET(request) {
  return handle(request);
}

export function POST(request) {
  return handle(request);
}

export default {
  fetch(request) {
    return handle(request);
  },
};
