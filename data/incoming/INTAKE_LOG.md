# Inbox intake log

## 2026-10-20 (automated intake, read-only on email)
- Scanned spraymapca inbox, last ~60 days (~83 threads).
- Records replies triaged: Placer (ingested), Kings (awaiting us: e-signed form), CV RWQCB R5 (partial delivery; WDR unit pending at the time; FTP posting 2026-10-07; see 2026-10-26 entry), Indian Valley CSD (delivered), Plumas Env Health (declined), Sierra Valley GMD (delivered; 10-14 follow-up answered), Plumas Public Works (no records; county does not spray), USFS R5 region-wide FOIA (acknowledged 2026-FS-R5-07596-F), CARB #26-332 (determination: disclosable, ~2026-10-26).
- No reply since 2026-09-23 from Caltrans D2 (portal filing still ours to do).
- data/records_requests.json: 10 rows updated, each note tagged "[intake 2026-10-20]".
- Raw attachments (26 files) held: box-only, git-ignored by design; listed in data/incoming/2026-10/MANIFEST.md.
- No personal contact details recorded in the repo.

## 2026-10-26 (Region 5 Water Board PRA reply)
- cvrwqcb-r5-all-stations: received (complete per agency 10/26), held, not ingested. Status stays `delivered`.
- Region 5 PRA reply 2026-10-26: the 2026-10-07 FTP posting includes all responsive records (WDR portion included); the posting expires 2026-11-11.
- SprayMap Data pulled the full posting 2026-10-21 (94 files, 42,693,978 bytes, NPS and WDR folders) and holds it off-repo with sha256 hashes. Raw files are not in git. Only the one-row Benner Creek hexazinone extract is committed (data/water/ceden_pra633_benner_qa.csv, PR #14).
- Per Region 5 PRA reply 10/26, WDR and NPS units do not test for hexazinone, imazapyr, glyphosate, aminopyralid.
- Unreconciled: the same PRA 633 CEDEN export has a hexazinone result at Benner Creek (518BENNER, 2022-10-03, 0.0013 ug/L, DNQ).
- No personal contact details recorded in the repo.
