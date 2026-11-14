-- 마산고 온라인 앨범 — 사진첩 나열 순서
-- 이미 운영 중인 서버에서 SQL Editor 에 통째로 붙여 넣고 한 번 Run. 다시 실행해도 안전하다. (contributor.sql 다음에 실행)
-- 예전에는 "늦게 올린 사진이 맨 앞"이라 마지막에 올린 한 장이 사진첩의 첫 화면이 됐다.
-- 이제는 행사 순서(수학여행 → 수련회 → 체육대회 → 교실 → 졸업앨범 → 졸업식 → 기타)로 묶고,
-- 같은 행사 안에서는 sort_order 가 작은 사진부터(단체사진 먼저), 번호가 없는 새 사진은 올린 순서대로 그 행사 맨 뒤에 붙는다.

alter table photos add column if not exists sort_order int;   -- 운영진이 매기는 순서 번호. 비어 있으면 그 행사 맨 뒤

-- 행사 분류에 '졸업앨범'(졸업앨범에 실린 반 단체·교실·조별 사진) 추가
alter table photos drop constraint if exists photos_event_check;
alter table photos add constraint photos_event_check check (event in ('수학여행','졸업식','수련회','체육대회','교실','졸업앨범','기타'));

create or replace function album_load(pw text) returns json
language plpgsql stable security definer set search_path = public, extensions as $$
begin
  if not album_check(pw) then raise exception 'wrong password' using errcode = '28000'; end if;
  return json_build_object(
    'roster',   coalesce((select json_agg(r order by r.id) from (select id, name, c3, portrait from roster) r), '[]'::json),
    'answers',  coalesce((select json_agg(a) from (select person_id, c1, c2 from answers) a), '[]'::json),
    'teachers', coalesce((select json_agg(t order by t.id) from (select id, name, role, subject, grade, class, portrait from teachers) t), '[]'::json),
    'photos',   coalesce((select json_agg(p order by array_position(array['수학여행','수련회','체육대회','교실','졸업앨범','졸업식','기타'], p.event), p.sort_order nulls last, p.created_at)
                          from (select id, path, event, caption, contributor, sort_order, created_at from photos where hidden = false) p), '[]'::json)
  );
end $$;

notify pgrst, 'reload schema';

-- 순서 번호를 매기려면 (예: 단체사진을 그 행사 맨 앞으로):
--   update photos set sort_order = 10 where id = '...';
