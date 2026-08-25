// Real-time PayPal IPN listener.
// PayPal POSTs here on each donation; we verify it, log the gift to Supabase
// (donation_events), and recompute per-effort totals (donation_totals) that the
// site reads live. Idempotent on txn_id.
//
// Vercel Node.js functions must use a Web fetch handler (or named HTTP method
// exports). A default (req, res) function that returns `new Response()` is
// ignored — POST then throws (`request.text is not a function`) and GET hangs
// until the 300s timeout, so IPN never lands.
//
// Required env (set in Vercel, server-side only):
//   SUPABASE_SERVICE_ROLE_KEY   Supabase service role key (bypasses RLS to write)
// Optional env:
//   SUPABASE_URL                defaults to the project URL below
//   PAYPAL_IPN_URL              live default; set to sandbox for testing
//   PAYPAL_RECEIVER             expected receiver_email/business (guards spoofing)

const SB_URL = process.env.SUPABASE_URL || 'https://aykhwsermojstiyrfcnv.supabase.co';
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
const IPN_VERIFY_URL = process.env.PAYPAL_IPN_URL || 'https://ipnpb.paypal.com/cgi-bin/webscr';
const EXPECTED_RECEIVER = (process.env.PAYPAL_RECEIVER || '').trim().toLowerCase();

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

function resolveEffort(p) {
  const bid = p.get('hosted_button_id') || p.get('item_number') || p.get('item_number1') || '';
  if (bid && BUTTON_EFFORT[bid]) return { effort: BUTTON_EFFORT[bid], button_id: bid };
  const nm = (p.get('item_name') || p.get('item_name1') || '').toLowerCase();
  for (const [needle, eff] of NAME_EFFORT) if (nm.includes(needle)) return { effort: eff, button_id: bid };
  return { effort: 'Unallocated', button_id: bid };
}

function timeoutSignal(ms) {
  if (typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function') {
    return AbortSignal.timeout(ms);
  }
  const c = new AbortController();
  setTimeout(() => c.abort(), ms);
  return c.signal;
}

export const config = { maxDuration: 30 };

async function handleIpn(request) {
  if (request.method !== 'POST') return new Response('paypal-ipn: POST only', { status: 200 });

  const raw = await request.text();

  let verdict = 'INVALID';
  try {
    const vr = await fetch(IPN_VERIFY_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'SprayMapCA-IPN/1.0' },
      body: 'cmd=_notify-validate&' + raw,
      signal: timeoutSignal(15000),
    });
    verdict = (await vr.text()).trim();
  } catch (e) {
    console.error('ipn verify error', e && e.message || e);
    return new Response('verify error', { status: 500 });
  }
  if (verdict !== 'VERIFIED') {
    console.warn('ipn not verified', verdict);
    return new Response('IPN ' + verdict, { status: 200 });
  }

  const p = new URLSearchParams(raw);

  if (EXPECTED_RECEIVER) {
    const rcv = (p.get('receiver_email') || p.get('business') || '').toLowerCase();
    if (rcv && rcv !== EXPECTED_RECEIVER) {
      console.warn('ipn receiver mismatch', rcv);
      return new Response('receiver mismatch', { status: 200 });
    }
  }

  const txnId = p.get('txn_id');
  if (!txnId) return new Response('no txn_id', { status: 200 });

  const { effort, button_id } = resolveEffort(p);
  const gross = parseFloat(p.get('mc_gross') || '0') || 0;
  const fee = parseFloat(p.get('mc_fee') || '0') || 0;
  const status = p.get('payment_status') || '';
  const row = {
    txn_id: txnId,
    effort,
    button_id: button_id || null,
    item_name: p.get('item_name') || null,
    gross,
    fee,
    net: +(gross - fee).toFixed(2),
    currency: p.get('mc_currency') || 'USD',
    status,
    source: 'ipn',
    raw: Object.fromEntries(p.entries()),
  };

  if (!SERVICE_KEY) return new Response('server not configured', { status: 500 });

  const ins = await fetch(SB_URL + '/rest/v1/donation_events', {
    method: 'POST',
    headers: {
      apikey: SERVICE_KEY,
      Authorization: 'Bearer ' + SERVICE_KEY,
      'Content-Type': 'application/json',
      Prefer: 'resolution=merge-duplicates',
    },
    body: JSON.stringify(row),
    signal: timeoutSignal(10000),
  });
  if (!ins.ok) {
    const t = await ins.text().catch(() => '');
    console.error('ipn store failed', ins.status, t.slice(0, 200));
    return new Response('store failed: ' + ins.status + ' ' + t.slice(0, 200), { status: 500 });
  }

  await fetch(SB_URL + '/rest/v1/rpc/recompute_donation_totals', {
    method: 'POST',
    headers: { apikey: SERVICE_KEY, Authorization: 'Bearer ' + SERVICE_KEY, 'Content-Type': 'application/json' },
    body: '{}',
    signal: timeoutSignal(10000),
  }).catch((e) => console.error('ipn recompute error', e && e.message || e));

  console.log('ipn ok', txnId, status, effort, gross);
  return new Response('OK', { status: 200 });
}

export function GET() {
  return new Response('paypal-ipn: POST only', { status: 200 });
}

export function POST(request) {
  return handleIpn(request);
}

export default {
  fetch(request) {
    return handleIpn(request);
  },
};
