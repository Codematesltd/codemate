-- Enable RLS on bookings table
alter table public.bookings enable row level security;

-- Create policies
create policy "Allow public insert"
on public.bookings for insert
to anon
with check (true);

create policy "Allow authenticated select"
on public.bookings for select
using (true);
