# Tahoe-area data-asks — 2026-09-19

Nothing sent. Review the drafts, then send.

## Gmail drafts (spraymapca)

1. **El Dorado + Alpine** — TO `eldcag@edcgov.us` — saved in Drafts (verified). Covers county codes 09 and 02 (Alpine pesticide permitting is handled by El Dorado).
2. **Placer** — TO `PlacerAg@placer.ca.gov` — body in `placer.txt`. Chrome closed before this draft persisted; paste/send from the outbox file.
3. **Nevada County** — TO `agdept@nevadacountyca.gov` — body in `nevada.txt`. Same: paste from outbox.
4. **Mendocino follow-up** (already in Drafts) — files were Sacramento code 34, not 23.
5. **2026-09-18 load summary** (already in Drafts).

## Letters in repo

- `records-requests/letters/26-el-dorado-alpine.md`
- `records-requests/letters/27-placer.md`
- `records-requests/letters/28-nevada.md`

Tracker rows `el-dorado`, `placer`, `nevada` set to **drafted**.

## Data loaded (no names yet)

Placer and Nevada **2022 PUR** were on disk (`udc22_31.txt`, `udc22_29.txt`) but missing from the live table. Loaded 25,062 application rows (`pur:2022:*`, ON CONFLICT DO NOTHING). Many lack PLSS so they will not all become map dots.

No public El Dorado/Placer/Nevada permit-name roster was found (no ArcGIS permittee layer). Names still need the PRA replies.

## After you send

El Dorado letter also covers Alpine. If El Dorado wants portal filing: https://eldoradocountyca.mycusthelp.com
