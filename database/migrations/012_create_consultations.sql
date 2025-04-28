create table if not exists consultations (
    id serial primary key,
    name text not null,
    email text not null,
    phone text not null,
    service text not null,
    query text not null,
    created_at timestamptz default now()
);

alter table consultations add column if not exists completed boolean default false;
