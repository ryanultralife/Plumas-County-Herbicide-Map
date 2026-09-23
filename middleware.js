/* Keep the headline number honest without hand edits.
 *
 * Link-preview scrapers (Facebook, X/Twitter, LinkedIn, Slack, Discord, iMessage, search bots) read the
 * page's <meta> tags and never run JavaScript, so a static "N million applications" goes stale every time
 * data is loaded. This middleware runs only for the home page and only for those bots: it asks the
 * database for the live mapped-application total (public map_totals() over the public map_agg view),
 * writes it into the description and og:description tags, and returns the page. Everyone else gets the
 * static file untouched; the on-page map stat is already computed live in the browser.
 *
 * Fails open: any error, and the static page is served as-is.
 */
export const config = { matcher: ['/'] };

const BOT = /facebookexternalhit|Facebot|Twitterbot|LinkedInBot|Slackbot|Discordbot|WhatsApp|TelegramBot|Pinterestbot|redditbot|Embedly|Applebot|Googlebot|bingbot|DuckDuckBot|Mastodon|Bluesky|SkypeUriPreview|iMessage/i;

const SB_URL = (typeof process !== 'undefined' && process.env && process.env.SUPABASE_URL) || 'https://aykhwsermojstiyrfcnv.supabase.co';
const SB_KEY = (typeof process !== 'undefined' && process.env && process.env.SUPABASE_ANON_KEY) || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF5a2h3c2VybW9qc3RpeXJmY252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA3OTY3NTcsImV4cCI6MjA2NjM3Mjc1N30.CNnnHXW3Xhl48cmRTvnyaaQcjLwc6itaFbeT2Zs-Awk';

let cache = { at: 0, mapped: 0 };
const TTL_MS = 60 * 60 * 1000;

async function liveMapped() {
  if (cache.mapped && Date.now() - cache.at < TTL_MS) return cache.mapped;
  try {
    const r = await fetch(SB_URL + '/rest/v1/rpc/map_totals', {
      method: 'POST',
      headers: { apikey: SB_KEY, Authorization: 'Bearer ' + SB_KEY, 'Content-Type': 'application/json' },
      body: '{}',
    });
    if (!r.ok) return cache.mapped;
    const j = await r.json();
    const n = Number(j && j.mapped);
    if (n > 1000000) cache = { at: Date.now(), mapped: n };
  } catch (e) { /* fail open */ }
  return cache.mapped;
}

function millions(n) {
  const m = n / 1e6;
  const s = m >= 10 ? m.toFixed(1).replace(/\.0$/, '') : m.toFixed(1);
  return s + ' million';
}

export default async function middleware(request) {
  try {
    const ua = request.headers.get('user-agent') || '';
    if (!BOT.test(ua)) return;                       // humans: static page, untouched
    const n = await liveMapped();
    if (!n) return;
    const origin = new URL(request.url).origin;
    const page = await fetch(origin + '/index.html', { headers: { 'x-spraymap-mw': '1' } });
    if (!page.ok) return;
    let html = await page.text();
    const txt = millions(n);
    html = html
      .replace(/(content="Interactive map of )[\d.,]+ million/, '$1' + txt)
      .replace(/(content=")[\d.,]+ million( reported pesticide applications mapped)/, '$1' + txt + '$2');
    return new Response(html, {
      status: 200,
      headers: {
        'content-type': 'text/html; charset=utf-8',
        'cache-control': 'public, max-age=0, s-maxage=3600',
        'x-spraymap-live-count': String(n),
      },
    });
  } catch (e) {
    return;                                          // fail open
  }
}
