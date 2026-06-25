#!/usr/bin/env bash
# Stream the local SQLite backup straight into Supabase Postgres (no giant CSV file).
# Prereqs: psql + python (uses build/export_csv.py; the sqlite3 CLI is NOT required).
# Schema must be applied first (supabase db push, or psql -f the migration).
#
#   DATABASE_URL='postgresql://postgres.aykhwsermojstiyrfcnv:<DB_PASSWORD>@aws-1-us-west-2.pooler.supabase.com:5432/postgres' \
#     bash build/load_supabase.sh [path/to/applications.sqlite]
#
# Get <DB_PASSWORD> from Supabase Dashboard > Project Settings > Database (or the
# POSTGRES_URL that the Vercel<>Supabase integration set).
set -euo pipefail
DB="${1:-/c/Users/ryanv/plumas_db_backup/applications.sqlite}"
: "${DATABASE_URL:?set DATABASE_URL to the Supabase connection string}"
COLS="app_id,source,region,date,year,lat,lon,county,land_type,owner,product,active_ingredient,amount,unit,method,activity,project,status,url,pulled"

# (optional) start clean:  psql "$DATABASE_URL" -c "truncate public.applications;"
# Fastest load: drop indexes first, COPY, then recreate (see migration for the index list).
python build/export_csv.py "$DB" \
  | psql "$DATABASE_URL" -c "\copy public.applications ($COLS) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')"

echo "Loaded. Verifying + building the map view + scores view:"
psql "$DATABASE_URL" -c "select count(*) rows, count(distinct chem_class) classes, count(distinct county) counties from public.applications;"
# build the public aggregated view the map reads:
psql "$DATABASE_URL" -f supabase/map_aggregate.sql
echo "Done. After future loads: psql \"\$DATABASE_URL\" -c 'refresh materialized view concurrently public.map_agg;'"
