-- rls_lockdown.sql | Supabase project aykhwsermojstiyrfcnv (SprayMap)
-- Applied 2026-10-20 as migration 'rls_lockdown_public_tables'.
-- Enables RLS + public SELECT-only policy and revokes write privileges from anon/authenticated
-- on loose public tables. Idempotent. Rollback: rls_lockdown_rollback.sql
-- recompute_donation_totals() is SECURITY DEFINER (owner bypasses RLS/grants) -> unaffected.

BEGIN;

ALTER TABLE public."operator_names" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "operator_names_public_read" ON public."operator_names";
CREATE POLICY "operator_names_public_read" ON public."operator_names" FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public."operator_names" FROM anon, authenticated;

ALTER TABLE public."_water_raw" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "_water_raw_public_read" ON public."_water_raw";
CREATE POLICY "_water_raw_public_read" ON public."_water_raw" FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public."_water_raw" FROM anon, authenticated;

ALTER TABLE public."_water" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "_water_public_read" ON public."_water";
CREATE POLICY "_water_public_read" ON public."_water" FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public."_water" FROM anon, authenticated;

ALTER TABLE public."_fix" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "_fix_public_read" ON public."_fix";
CREATE POLICY "_fix_public_read" ON public."_fix" FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public."_fix" FROM anon, authenticated;

ALTER TABLE public."_places" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "_places_public_read" ON public."_places";
CREATE POLICY "_places_public_read" ON public."_places" FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public."_places" FROM anon, authenticated;

ALTER TABLE public."_conf" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "_conf_public_read" ON public."_conf";
CREATE POLICY "_conf_public_read" ON public."_conf" FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public."_conf" FROM anon, authenticated;

ALTER TABLE public."_fix3" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "_fix3_public_read" ON public."_fix3";
CREATE POLICY "_fix3_public_read" ON public."_fix3" FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public."_fix3" FROM anon, authenticated;

ALTER TABLE public."_null_sect" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "_null_sect_public_read" ON public."_null_sect";
CREATE POLICY "_null_sect_public_read" ON public."_null_sect" FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public."_null_sect" FROM anon, authenticated;

ALTER TABLE public."donation_baseline" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "donation_baseline_public_read" ON public."donation_baseline";
CREATE POLICY "donation_baseline_public_read" ON public."donation_baseline" FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public."donation_baseline" FROM anon, authenticated;

ALTER TABLE public."_fix_new" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "_fix_new_public_read" ON public."_fix_new";
CREATE POLICY "_fix_new_public_read" ON public."_fix_new" FOR SELECT TO anon, authenticated USING (true);
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public."_fix_new" FROM anon, authenticated;

COMMIT;

-- spatial_ref_sys (PostGIS, owner supabase_admin): the following was executed separately but was a
-- silent no-op (grants were made by supabase_admin; postgres cannot revoke them). anon/authenticated
-- still hold DML on spatial_ref_sys. Needs Supabase support / supabase_admin to fix.
-- REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES ON public.spatial_ref_sys FROM anon, authenticated;
