-- Enable storage extension if not already enabled
create extension if not exists "storage";

-- Set up storage policies
create policy "Allow public access"
on storage.objects for select
to public
using (bucket_id = 'refrence');

create policy "Enable storage for users and anon"
on storage.buckets for select
to public
using (true);

create policy "Enable insert for authenticated users and anon" 
on storage.buckets for insert
to public
with check (true);

create policy "Enable all for authenticated users and anon"
on storage.objects for all 
to public
using (bucket_id = 'refrence');

-- Update existing bucket or create new one
do $$
begin
    if not exists (select * from storage.buckets where id = 'refrence') then
        insert into storage.buckets (id, name, public) values ('refrence', 'refrence', true);
    end if;
end $$;

-- Grant necessary permissions
grant usage on schema storage to postgres, anon, authenticated, service_role;
grant all privileges on all tables in schema storage to postgres, anon, authenticated, service_role;
grant all privileges on all sequences in schema storage to postgres, anon, authenticated, service_role;
