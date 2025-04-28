-- Allow authenticated users to upload (insert) and read (select) files in the 'refrence' bucket
create policy "Allow authenticated upload to refrence"
on storage.objects for insert
to authenticated
with check (bucket_id = 'refrence');

create policy "Allow authenticated read from refrence"
on storage.objects for select
to authenticated
using (bucket_id = 'refrence');

-- Allow public (anon) read access to files in the 'refrence' bucket
create policy "Allow public read from refrence"
on storage.objects for select
to anon
using (bucket_id = 'refrence');
