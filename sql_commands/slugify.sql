-- original source: https://medium.com/adhawk-engineering/using-postgresql-to-generate-slugs-5ec9dd759e88

-- https://www.postgresql.org/docs/9.6/unaccent.html
CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;

-- create the function in the public schema
CREATE OR REPLACE FUNCTION public.slugify(
  v TEXT
) RETURNS TEXT
  LANGUAGE plpgsql
  STRICT IMMUTABLE AS
$function$
BEGIN
  -- 1. trim trailing and leading whitespaces from text
  -- 2. remove accents (diacritic signs) from a given text
  -- 3. lowercase unaccented text
  -- 4. replace non-alphanumeric (excluding hyphen, underscore) with a hyphen
  -- 5. trim leading and trailing hyphens
  RETURN trim(BOTH '-' FROM regexp_replace(lower(public.unaccent(trim(v))), '[^a-z0-9\\-_]+', '-', 'gi'));
END;
$function$;