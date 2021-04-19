CREATE OR REPLACE FUNCTION public.slugify_array(input_arr TEXT[]) RETURNS TEXT[]
  LANGUAGE plpgsql
  STRICT IMMUTABLE AS
$function$
DECLARE
	item text;
	new_arr text[] := '{}';
BEGIN
	FOREACH item IN ARRAY input_arr LOOP
		item := slugify(item);
		new_arr := new_arr || item;
	END LOOP;
	RETURN new_arr;
END;
$function$;