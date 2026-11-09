-- 마산고 온라인 앨범 — 공유 비밀번호 잠금
-- schema.sql 다음에 실행. 사이트는 이 파일의 함수로만 데이터를 읽고 쓴다.
-- 비밀번호는 해시로만 저장되고, 표를 직접 읽는 길은 모두 막는다.

create extension if not exists pgcrypto with schema extensions;

-- 설정 표: 정책이 없으므로 사이트에서는 읽을 수 없다
create table if not exists album_settings (
  key   text primary key,
  value text not null
);
alter table album_settings enable row level security;

-- 비밀번호 정하기/바꾸기 (SQL Editor 에서만 실행; 저장소에는 넣지 않는다)
--   insert into album_settings (key, value) values ('password', extensions.crypt('여기에비밀번호', extensions.gen_salt('bf')))
--   on conflict (key) do update set value = excluded.value;

create or replace function album_check(pw text) returns boolean
language sql stable security definer set search_path = public, extensions as $$
  select exists (
    select 1 from album_settings
    where key = 'password' and value = crypt(coalesce(pw, ''), value)
  );
$$;

-- 앨범 전체 읽기
create or replace function album_load(pw text) returns json
language plpgsql stable security definer set search_path = public, extensions as $$
begin
  if not album_check(pw) then raise exception 'wrong password' using errcode = '28000'; end if;
  return json_build_object(
    'roster',   coalesce((select json_agg(r order by r.id) from (select id, name, c3, portrait from roster) r), '[]'::json),
    'answers',  coalesce((select json_agg(a) from (select person_id, c1, c2 from answers) a), '[]'::json),
    'teachers', coalesce((select json_agg(t order by t.id) from (select id, name, role, subject, grade, class, portrait from teachers) t), '[]'::json),
    'photos',   coalesce((select json_agg(p order by p.created_at desc) from (select id, path, event, caption, created_at from photos where hidden = false) p), '[]'::json)
  );
end $$;

-- 1·2학년 반 저장
create or replace function album_set_answer(pw text, p_person text, p_c1 int, p_c2 int) returns void
language plpgsql security definer set search_path = public, extensions as $$
begin
  if not album_check(pw) then raise exception 'wrong password' using errcode = '28000'; end if;
  if not exists (select 1 from roster where id = p_person) then raise exception 'no such person'; end if;
  insert into answers (person_id, c1, c2) values (p_person, p_c1, p_c2)
  on conflict (person_id) do update set c1 = excluded.c1, c2 = excluded.c2;
end $$;

-- 사진첩에 사진 등록 (파일은 storage 에 먼저 올린 뒤)
create or replace function album_add_photo(pw text, p_path text, p_event text, p_caption text) returns void
language plpgsql security definer set search_path = public, extensions as $$
begin
  if not album_check(pw) then raise exception 'wrong password' using errcode = '28000'; end if;
  insert into photos (path, event, caption) values (p_path, p_event, nullif(p_caption, ''));
end $$;

-- 사이트(anon)는 함수만 쓸 수 있고, 표는 직접 못 읽는다
drop policy if exists "roster read"     on roster;
drop policy if exists "answers read"    on answers;
drop policy if exists "answers insert"  on answers;
drop policy if exists "answers update"  on answers;
drop policy if exists "photos read"     on photos;
drop policy if exists "photos insert"   on photos;
drop policy if exists "teachers read"   on teachers;

grant execute on function album_check(text), album_load(text),
  album_set_answer(text, text, int, int), album_add_photo(text, text, text, text) to anon, authenticated;

-- 사진 파일: 버킷 목록 조회는 정책이 없어 막혀 있고, 경로는 무작위라 추측할 수 없다.
-- 경로는 비밀번호를 통과한 album_load 로만 알 수 있다.
