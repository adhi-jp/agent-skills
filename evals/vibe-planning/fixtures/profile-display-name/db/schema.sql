create table users (
  id uuid primary key,
  email text not null unique,
  display_name text
);
