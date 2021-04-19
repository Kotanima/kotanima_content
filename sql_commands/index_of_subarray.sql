create or replace function index_of_subarray(arr anyarray, sub anyarray)
returns integer language plpgsql immutable as $$
begin
    for i in 1 .. cardinality(arr)- cardinality(sub)+ 1 loop
        if arr[i:i+ cardinality(sub)- 1] = sub then
            return i;
        end if;
    end loop;
    return 0;
end $$;