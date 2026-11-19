-- 마산고 온라인 앨범 — 사진에 "AI 복원본" 칸 추가
-- 이미 운영 중인 서버에서 SQL Editor 에 통째로 붙여 넣고 한 번 Run. 다시 실행해도 안전하다. (grade.sql 다음에 실행)
-- ai_path 가 있는 사진은 크게 볼 때 원래 사진과 AI 복원본을 나란히 보여 준다.
-- AI 복원본은 AI 가 새로 그린 그림이라 얼굴이 실제와 다를 수 있다. 그래서 원래 사진을 대신하지 않고 항상 함께 보여 준다.

alter table photos add column if not exists ai_path text;   -- storage 버킷 'photos' 안의 AI 복원본 경로. 비어 있으면 없음

create or replace function album_load(pw text) returns json
language plpgsql stable security definer set search_path = public, extensions as $$
begin
  if not album_check(pw) then raise exception 'wrong password' using errcode = '28000'; end if;
  return json_build_object(
    'roster',   coalesce((select json_agg(r order by r.id) from (select id, name, c3, portrait from roster) r), '[]'::json),
    'answers',  coalesce((select json_agg(a) from (select person_id, c1, c2 from answers) a), '[]'::json),
    'teachers', coalesce((select json_agg(t order by t.id) from (select id, name, role, subject, grade, class, portrait from teachers) t), '[]'::json),
    'photos',   coalesce((select json_agg(p order by array_position(array['수학여행','수련회','체육대회','교실','졸업앨범','졸업식','기타'], p.event), p.sort_order nulls last, p.created_at)
                          from (select id, path, ai_path, event, caption, contributor, sort_order, grade, created_at from photos where hidden = false) p), '[]'::json)
  );
end $$;

notify pgrst, 'reload schema';

-- AI 복원본을 붙이려면 (파일은 photos 버킷에 먼저 올린다):
--   update photos set ai_path = '날짜/파일.jpg' where id = '...';
