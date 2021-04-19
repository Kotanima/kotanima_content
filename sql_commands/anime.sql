CREATE TABLE anime
(
    title text DEFAULT NOT NULL,
    anime_id integer NOT NULL,
    image_path text,
    mpaa_rating text,
    title_japanese text,
    title_english text,
    title_russian text,
    title_synonyms text[],
    genres text[],
    studios text[],
    is_airing boolean,
    franchise text
)

CREATE TABLE non_anime
(
    id SERIAL PRIMARY KEY,
    title text NOT NULL,
    title_japanese text,
    title_english text,
    title_russian text,
    title_synonyms text[],
    genres text[],
    franchise text
)

CREATE INDEX non_anime_lower_idx
    ON public.non_anime USING btree
    (lower(title) COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: animes_lower_idx1

-- DROP INDEX public.animes_lower_idx1;

CREATE INDEX non_anime_lower_idx1
    ON public.non_anime USING btree
    (lower(title_english) COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: animes_replace_idx

-- DROP INDEX public.animes_replace_idx;

CREATE INDEX non_anime_replace_idx
    ON public.non_anime USING btree
    (replace(franchise, '_'::text, ''::text) COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: animes_slugify_array_idx

-- DROP INDEX public.animes_slugify_array_idx;

CREATE INDEX non_anime_slugify_array_idx
    ON public.non_anime USING btree
    (slugify_array(title_synonyms) COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: animes_slugify_idx

-- DROP INDEX public.animes_slugify_idx;

CREATE INDEX non_anime_slugify_idx
    ON public.non_anime USING btree
    (slugify(title) COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: animes_slugify_idx1

-- DROP INDEX public.animes_slugify_idx1;

CREATE INDEX non_anime_slugify_idx1
    ON public.non_anime USING btree
    (slugify(title_english) COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: animes_string_to_array_idx

-- DROP INDEX public.animes_string_to_array_idx;

CREATE INDEX non_anime_string_to_array_idx
    ON public.non_anime USING gin
    (string_to_array(franchise, '_'::text) COLLATE pg_catalog."default")
    TABLESPACE pg_default;
-- Index: idx_animes_anime_id

-- DROP INDEX public.idx_animes_anime_id;

CREATE INDEX idx_non_anime_anime_id
    ON public.non_anime USING btree
    (anime_id ASC NULLS LAST)
    TABLESPACE pg_default;