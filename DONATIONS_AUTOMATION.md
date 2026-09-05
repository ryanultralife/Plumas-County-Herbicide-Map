# Auto-updating donation totals (real-time + daily)

> **Status 2026-09-05: LIVE.** PayPal IPN enabled at `https://www.spraymapca.org/api/paypal-ipn`,
> service-role key present in Vercel, daily cron confirmed firing 08:00 UTC. Only the optional
> PayPal REST backfill (`PAYPAL_CLIENT_ID/SECRET`) remains unset.

The per-effort donation figures shown on the site (Donate modal + Transparency
tab "Donations received — by effort") update **automatically** from PayPal —
no more hand-editing.

## How it works

```
Donor gives on a PayPal donation page
        │
        ├─(real-time)→  PayPal IPN  →  /api/paypal-ipn  →  Supabase
        │                                  (verify, log event, recompute)
        └─(daily 08:00 UTC)→ Vercel Cron → /api/reconcile-donations → Supabase
                                           (backfill any misses, recompute)
        │
   Supabase  public.donation_totals   ← the site reads this live (anon key)
```

- **`public.donation_totals`** — one row per effort (`gross`, `net`, `count`, `updated_at`). The site reads it with the existing public anon key. Public read-only (RLS).
- **`public.donation_events`** — one row per gift (idempotent on PayPal `txn_id`), stores the full raw payload. Private (no anon access).
- **`public.donation_baseline`** — the pre-automation figure ($5 Water testing gift received 2026-08-10, before the webhook existed).
- **`recompute_donation_totals()`** — RPC that sets `donation_totals = baseline + sum(Completed events)`. Both functions call it, so totals are always consistent.

Schema is in `build/donations_schema.sql` + `build/donations_schema_v2.sql` (already applied).

The site (`index.html`) fetches `donation_totals` on load / when the Donate modal
or Transparency tab opens. If Supabase is unreachable it falls back to the
hard-coded snapshot in `DONATE_CONFIG`, so the page never breaks.

## One-time setup you must do (I can't enter credentials)

### 1. Vercel environment variables
Vercel → your project → **Settings → Environment Variables** (Production).

| Name | Value | Needed for |
|---|---|---|
| `SUPABASE_SERVICE_ROLE_KEY` | **Already set** (added by the Supabase integration, Jun 24) | **Required** — lets the functions write |
| `CRON_SECRET` | any long random string | Protects the daily endpoint (Vercel Cron sends it automatically) |
| `PAYPAL_RECEIVER` | `spraymapca@gmail.com` | Optional anti-spoof guard on IPN |
| `PAYPAL_CLIENT_ID` | from a PayPal REST app (below) | Optional — enables the daily PayPal backfill |
| `PAYPAL_CLIENT_SECRET` | from the same app | Optional — enables the daily PayPal backfill |

**After adding env vars, redeploy** (Deployments → ⋯ → Redeploy) so the functions pick them up.

### 2. Turn on PayPal IPN (real-time)
PayPal (business account) → **Account Settings → Notifications → Instant payment
notifications → Update**:
- **Notification URL:** `https://spraymapca.org/api/paypal-ipn`
- Set to **Receive IPN messages (Enabled)** → Save.

That's it — every future donation now updates the site within seconds. (The
existing $5 gift is already counted via the baseline; it won't re-fire.)

### 3. (Optional) PayPal REST app for the daily backfill
Only needed if you want the daily job to *catch* any donation that somehow missed
its IPN. developer.paypal.com → **Apps & Credentials → Live → Create App**:
- Copy the **Client ID** and **Secret** into the Vercel env vars above.
- In the app's features, enable **Transaction Search**.

Without this, the daily cron still runs and keeps totals consistent
(baseline + logged events); it just won't discover a gift that never sent an IPN.

## Verify it's live
1. Make a small real donation on the SprayMap page ($1), then refund it in PayPal.
   Within a few seconds the site totals should tick up; `donation_events` gets a row.
2. Daily cron: Vercel → Deployments → the cron function's logs (runs 08:00 UTC),
   or open `https://spraymapca.org/api/reconcile-donations` (returns JSON; needs the
   `CRON_SECRET` header if set).

## Notes
- **Security:** the service-role key and PayPal secret live **only** in Vercel env
  (server-side). The client HTML keeps only the public anon key.
- **Attribution:** each effort is a distinct PayPal hosted button; the IPN function
  maps `hosted_button_id` → effort, falling back to the item name. It saves the full
  raw payload, so after the first live gift we can confirm the exact field and tighten
  the mapping if ever needed. Anything unmatched is logged as `Unallocated` (never lost).
- **Gross vs. net:** the site shows **gross** ("amount raised", matching PayPal's
  dashboard). A new-account funds *hold* affects when money is withdrawable, not the
  raised total.
- **Manual override:** to correct a figure by hand, edit `public.donation_baseline`
  then run `select public.recompute_donation_totals();`.
