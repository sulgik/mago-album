-- 마산고 온라인 앨범 — 사진에 "몇 학년 때 사진인지" 칸 추가
-- 이미 운영 중인 서버에서 SQL Editor 에 통째로 붙여 넣고 한 번 Run. 다시 실행해도 안전하다. (order.sql 다음에 실행)
-- 학년이 적힌 사진은 사진첩뿐 아니라, 사진 주인(제공자)의 그 학년 반 화면(졸업앨범 탭)에도 함께 나온다.
-- 수학여행 사진은 칸이 비어 있어도 화면에서 2학년으로 본다(config.js 의 EVENT_GRADE).

alter table photos add column if not exists grade int check (grade between 1 and 3);   -- 비어 있으면 학년 모름

create or replace function album_load(pw text) returns json
language plpgsql stable security definer set search_path = public, extensions as $$
begin
  if not album_check(pw) then raise exception 'wrong password' using errcode = '28000'; end if;
  return json_build_object(
    'roster',   coalesce((select json_agg(r order by r.id) from (select id, name, c3, portrait from roster) r), '[]'::json),
    'answers',  coalesce((select json_agg(a) from (select person_id, c1, c2 from answers) a), '[]'::json),
    'teachers', coalesce((select json_agg(t order by t.id) from (select id, name, role, subject, grade, class, portrait from teachers) t), '[]'::json),
    'photos',   coalesce((select json_agg(p order by array_position(array['수학여행','수련회','체육대회','교실','졸업앨범','졸업식','기타'], p.event), p.sort_order nulls last, p.created_at)
                          from (select id, path, event, caption, contributor, sort_order, grade, created_at from photos where hidden = false) p), '[]'::json)
  );
end $$;

notify pgrst, 'reload schema';

-- 학년을 적으려면 (예: 2학년 말 교실 사진):
--   update photos set grade = 2 where id = '...';
