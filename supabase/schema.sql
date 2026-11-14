-- 마산고 온라인 앨범 — Supabase 스키마
-- Supabase 대시보드 > SQL Editor 에 통째로 붙여 넣고 Run.
-- 다시 실행해도 안전하도록 if not exists / or replace 를 쓴다.

-- 1) 졸업생 명단: 이름 + 3학년 반 (졸업앨범 기준). 운영진만 넣는다.
create table if not exists roster (
  id         text primary key,          -- 예: '3-02-07' (학년-반-번호) 또는 아무 고유값
  name       text not null,
  c3         int  check (c3 between 1 and 30),
  created_at timestamptz default now()
);

-- 2) 동문이 채우는 1·2학년 반
create table if not exists answers (
  person_id  text primary key references roster(id) on delete cascade,
  c1         int check (c1 between 1 and 30),
  c2         int check (c2 between 1 and 30),
  updated_at timestamptz default now()
);

-- 2-1) 변경 이력: 누가 장난으로 바꿔도 되돌릴 수 있게 모든 변경을 남긴다
create table if not exists answers_log (
  id         bigserial primary key,
  person_id  text,
  c1         int,
  c2         int,
  at         timestamptz default now()
);

create or replace function log_answer() returns trigger language plpgsql security definer as $$
begin
  insert into answers_log(person_id, c1, c2) values (new.person_id, new.c1, new.c2);
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists answers_log_trg on answers;
create trigger answers_log_trg before insert or update on answers
  for each row execute function log_answer();

-- 3) 사진첩
create table if not exists photos (
  id         uuid primary key default gen_random_uuid(),
  path       text not null,             -- storage 버킷 'photos' 안의 경로
  event      text not null check (event in ('수학여행','졸업식','수련회','체육대회','교실','기타')),
  caption    text check (char_length(caption) <= 200),
  contributor text check (char_length(contributor) <= 40),   -- 사진 주인(제공자) 이름. 사진첩을 이 기준으로 나눈다
  hidden     boolean default false,     -- 운영진이 true 로 바꾸면 사이트에서 숨김
  created_at timestamptz default now()
);

-- ---------- 접근 규칙 (RLS) ----------
alter table roster      enable row level security;
alter table answers     enable row level security;
alter table answers_log enable row level security;
alter table photos      enable row level security;

drop policy if exists "roster read"   on roster;
create policy "roster read"   on roster  for select using (true);
-- roster 는 쓰기 정책이 없으므로 사이트에서는 못 바꾼다 (대시보드·SQL 로만)

drop policy if exists "answers read"   on answers;
drop policy if exists "answers insert" on answers;
drop policy if exists "answers update" on answers;
create policy "answers read"   on answers for select using (true);
create policy "answers insert" on answers for insert with check (true);
create policy "answers update" on answers for update using (true) with check (true);
-- answers_log 는 정책 없음 → 사이트에서는 읽기·쓰기 불가, 운영진만 대시보드에서 본다

drop policy if exists "photos read"   on photos;
drop policy if exists "photos insert" on photos;
create policy "photos read"   on photos for select using (hidden = false);
create policy "photos insert" on photos for insert with check (hidden = false);

-- ---------- 사진 파일 저장소 ----------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('photos', 'photos', true, 5242880, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = true, file_size_limit = 5242880,
  allowed_mime_types = array['image/jpeg','image/png','image/webp'];

drop policy if exists "photos upload" on storage.objects;
create policy "photos upload" on storage.objects for insert
  with check (bucket_id = 'photos');

-- ---------- 개인 사진 (졸업앨범 증명사진) ----------
-- 운영진만 올린다: 버킷 'portraits' 는 공개 읽기, 사이트에서 올리기 정책 없음.
alter table roster add column if not exists portrait text;   -- 'portraits' 버킷 안의 경로, 예: '3-02-01.jpg'
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('portraits', 'portraits', true, 2097152, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = true;

-- ---------- 선생님 (담임·교과) ----------
-- 운영진만 넣는다. 사진은 'portraits' 버킷, 예: 't-jeonghuisang.jpg'
create table if not exists teachers (
  id         text primary key,          -- 예: 't-01'
  name       text not null,
  role       text not null check (role in ('담임','교과')),
  subject    text,                      -- 교과 (예: 수학). 담임도 적어 두면 함께 표시
  grade      int  check (grade between 1 and 3),   -- 담임/교과를 맡은 학년
  class      int  check (class between 1 and 30),  -- 담임 반 (교과는 비움)
  portrait   text,
  created_at timestamptz default now()
);
alter table teachers enable row level security;
drop policy if exists "teachers read" on teachers;
create policy "teachers read" on teachers for select using (true);

-- 선생님 넣기 (SQL Editor 에서만; 실명은 저장소에 두지 않는다)
--   insert into teachers (id, name, role, grade, class) values ('t-01', '이름', '담임', 3, 2)
--   on conflict (id) do update set name = excluded.name, role = excluded.role, grade = excluded.grade, class = excluded.class;
