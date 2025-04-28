-- Enable storage
create extension if not exists "storage";

-- Create bucket for reference images
insert into storage.buckets (id, name, public)
values ('refrence', 'refrence', true);

-- Set up storage policies
create policy "Public Access"
on storage.objects for select
using ( bucket_id = 'refrence' );

create policy "Auth Upload"
on storage.objects for insert
with check (
  bucket_id = 'refrence' 
  and auth.role() = 'authenticated'
  and (storage.foldername(name))[1] = 'public'
);
