-- SprayMap CA — base schema for the statewide pesticide-use data.
-- Run via `supabase db push` (or paste into the SQL editor).
-- chem_class is DERIVED via the immutable function below (used by map_aggregate.sql and
-- a functional index) — NOT stored as a generated column, so the bulk COPY load stays fast.

-- ---------- chemical-class helper (immutable) ----------
-- Class names match map.html CLASS_COLORS: herbicide, insecticide, fungicide, fumigant,
-- rodenticide, growth_regulator, adjuvant, other, unknown.
create or replace function public.chem_class(ai text)
returns text language sql immutable as $$
  select case
    when ai is null or ai = '' then 'unknown'
    when upper(ai) ~ 'GLYPHOSATE|GLUFOSINATE|OXYFLUORFEN|PENDIMETHALIN|INDAZIFLAM|RIMSULFURON|SAFLUFENACIL|CLETHODIM|SETHOXYDIM|CARFENTRAZONE|PYRAFLUFEN|TRIFLURALIN|PARAQUAT|DIURON|2,4-D|DICAMBA|ATRAZINE|SIMAZINE|METOLACHLOR|FLUMIOXAZIN|HALOSULFURON|IMAZAPYR|IMAZAMOX|TRICLOPYR|CLOPYRALID|AMINOPYRALID|HEXAZINONE|NORFLURAZON|BROMACIL|FLAZASULFURON|SULFOMETURON|NAPROPAMIDE|METRIBUZIN|LINURON|PRODIAMINE|ISOXABEN|MESOTRIONE|FLUROXYPYR|\mMCPA\M|BENTAZON|PRONAMIDE|DIQUAT' then 'herbicide'
    when upper(ai) ~ '\-THRIN|\-CLOPRID|IMIDACLOPRID|ABAMECTIN|SPINOSAD|SPINETORAM|SPIROTETRAMAT|FIPRONIL|INDOXACARB|CHLORANTRANILIPROLE|METHOXYFENOZIDE|DINOTEFURAN|THIAMETHOXAM|METHOMYL|ACETAMIPRID|PYRIPROXYFEN|SULFOXAFLOR|CYANTRANILIPROLE|FLUPYRADIFURONE|PYRETHRIN|AZADIRACHTIN|MALATHION|CHLORPYRIFOS|CARBARYL|OXAMYL|DIAZINON|BUPROFEZIN|ETOXAZOLE|BIFENAZATE|FLONICAMID|EMAMECTIN|SPIRODICLOFEN|HEXYTHIAZOX|PYMETROZINE|ESFENVALERATE|ACEPHATE|DIMETHOATE|NOVALURON|NALED' then 'insecticide'
    when upper(ai) ~ '\-STROBIN|\-CONAZOLE|AZOXYSTROBIN|MANCOZEB|CHLOROTHALONIL|COPPER|SULFUR|PHOSPHITE|BOSCALID|FLUOPYRAM|CAPTAN|MYCLOBUTANIL|FLUDIOXONIL|IPRODIONE|METALAXYL|MEFENOXAM|CYPRODINIL|FENHEXAMID|ZIRAM|THIOPHANATE|FLUAZINAM|PENTHIOPYRAD|MANDIPROPAMID|CYAZOFAMID|FOSETYL|DODINE' then 'fungicide'
    when upper(ai) ~ 'DIPHACINONE|BRODIFACOUM|BROMADIOLONE|CHLOROPHACINONE|WARFARIN|ZINC PHOSPHIDE|CHOLECALCIFEROL|DIFETHIALONE|STRYCHNINE' then 'rodenticide'
    when upper(ai) ~ '1,3-DICHLOROPROPENE|METAM|CHLOROPICRIN|DAZOMET|METHYL BROMIDE|TELONE|DITHIOCARBAMATE' then 'fumigant'
    when upper(ai) ~ 'MINERAL OIL|PETROLEUM|\mSOAP\M|KAOLIN|FATTY ACID|SPRAY OIL' then 'adjuvant'
    when upper(ai) ~ 'GIBBERELL|ETHEPHON|PACLOBUTRAZOL|ABSCISIC|MEPIQUAT|TRINEXAPAC' then 'growth_regulator'
    else 'other' end;
$$;

-- ---------- the unified application records (one row = one reported application) ----------
create table if not exists public.applications (
  app_id            text primary key,
  source            text,
  region            text,
  date              text,
  year              integer,
  lat               double precision,
  lon               double precision,
  county            text,
  land_type         text,
  owner             text,
  product           text,
  active_ingredient text,
  amount            double precision,
  unit              text,
  method            text,
  activity          text,
  project           text,
  status            text,
  url               text,
  pulled            text
);
create index if not exists ix_app_region on public.applications(region);
create index if not exists ix_app_county on public.applications(county);
create index if not exists ix_app_year   on public.applications(year);
create index if not exists ix_app_source on public.applications(source);
create index if not exists ix_app_class  on public.applications(public.chem_class(active_ingredient));
create index if not exists ix_app_land   on public.applications(land_type);
create index if not exists ix_app_ll     on public.applications(lat, lon);

-- Keep the raw table PRIVATE (RLS, no anon grant). The public map reads only the
-- aggregated map_agg view (created in map_aggregate.sql) via the anon key.
alter table public.applications enable row level security;

-- Fast bulk load: create table only (no indexes), COPY, then create indexes + the view.
--   \copy public.applications (app_id,source,region,date,year,lat,lon,county,land_type,owner,product,active_ingredient,amount,unit,method,activity,project,status,url,pulled) FROM 'applications.csv' CSV HEADER
