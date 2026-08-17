// Daily reconciliation safety net (Vercel Cron -> GET).
// Always: recompute donation_totals = baseline + sum(Completed events).
// If PayPal REST creds are present: also backfill any events that never arrived
// via IPN (e.g. a webhook outage) by scanning the last ~31 days of transactions,
// then recompute. Backfill is best-effort and never blocks the recompute.
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

const BUTTON_EFFORT = {
  '9Y4PFVUKA8ECJ': 'SprayMap California',
  '933QFJD3Q4PZL': 'Water testing',
  'DVX547VFHJXJW': 'Goat grazing',
};
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

async function ppToken() {
  const auth = Buffer.from(PP_ID + ':' + PP_SECRET).toString('base64');
  const r = await fetch(PP_BASE + '/v1/oauth2/token', {
    method: 'POST',
    headers: { Authorization: 'Basic ' + auth, 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'grant_type=client_credentials',
  });
  if (!r.ok) throw new Error('paypal token ' + r.status);
  return (await r.json()).access_token;
}

// Pull the last ~31 days of transactions and upsert any missing events (ignore-duplicates
// so IPN-sourced rows stay authoritative). Returns how many rows were sent.
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
  });
  if (!r.ok) throw new Error('transaction search ' + r.status);
  const data = await r.json();
  const txns = data.transaction_details || [];
  const rows = [];
  for (const t of txns) {
    const info = t.transaction_info || {};
    if (info.transaction_status !== 'S') continue; // S = success/completed
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
      Prefer: 'resolution=ignore-duplicates', // don't clobber IPN-sourced rows
    },
    body: JSON.stringify(rows),
  });
  if (!up.ok) throw new Error('event upsert ' + up.status);
  return rows.length;
}

async function recompute() {
  await fetch(SB_URL + '/rest/v1/rpc/recompute_donation_totals', {
    method: 'POST',
    headers: { apikey: SERVICE_KEY, Authorization: 'Bearer ' + SERVICE_KEY, 'Content-Type': 'application/json' },
    body: '{}',
  });
}

export default async function handler(request) {
  if (CRON_SECRET) {
    const auth = request.headers.get('authorization') || '';
    if (auth !== 'Bearer ' + CRON_SECRET) return new Response('Unauthorized', { status: 401 });
  }
  if (!SERVICE_KEY) return new Response('server not configured', { status: 500 });

  let scanned = 0, ppError = null;
  if (PP_ID && PP_SECRET) {
    try { scanned = await backfillFromPayPal(); }
    catch (e) { ppError = String(e && e.message || e); } // non-fatal
  }
  await recompute();

  return new Response(JSON.stringify({ ok: true, backfill_scanned: scanned, paypal: PP_ID ? (ppError || 'ok') : 'disabled' }), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  });
}
