-- 마산고 온라인 앨범 — 사진첩에 "사진 주인(제공자)" 추가
-- 이미 운영 중인 서버에서 SQL Editor 에 통째로 붙여 넣고 한 번 Run. 다시 실행해도 안전하다.
-- 같은 행사 사진이라도 사진 주인마다 반이 달라서, 사진첩을 사진 주인 기준으로 나눠 보여 주기 위한 칸이다.

alter table photos add column if not exists contributor text check (char_length(contributor) <= 40);

create or replace function album_load(pw text) returns json
language plpgsql stable security definer set search_path = public, extensions as $$
begin
  if not album_check(pw) then raise exception 'wrong password' using errcode = '28000'; end if;
  return json_build_object(
    'roster',   coalesce((select json_agg(r order by r.id) from (select id, name, c3, portrait from roster) r), '[]'::json),
    'answers',  coalesce((select json_agg(a) from (select person_id, c1, c2 from answers) a), '[]'::json),
    'teachers', coalesce((select json_agg(t order by t.id) from (select id, name, role, subject, grade, class, portrait from teachers) t), '[]'::json),
    'photos',   coalesce((select json_agg(p order by p.created_at desc) from (select id, path, event, caption, contributor, created_at from photos where hidden = false) p), '[]'::json)
  );
end $$;

-- 사진 등록: 제공자 이름을 함께 받는다. 옛 화면(제공자 없이 호출)도 그대로 동작한다.
drop function if exists album_add_photo(text, text, text, text);
create or replace function album_add_photo(pw text, p_path text, p_event text, p_caption text, p_contributor text default null) returns void
language plpgsql security definer set search_path = public, extensions as $$
begin
  if not album_check(pw) then raise exception 'wrong password' using errcode = '28000'; end if;
  insert into photos (path, event, caption, contributor)
  values (p_path, p_event, nullif(p_caption, ''), nullif(btrim(p_contributor), ''));
end $$;

grant execute on function album_add_photo(text, text, text, text, text) to anon, authenticated;
notify pgrst, 'reload schema';

-- 이미 올라간 사진에 제공자를 적어 넣으려면 (예):
--   update photos set contributor = '이름' where created_at::date = '2026-11-09' and contributor is null;
