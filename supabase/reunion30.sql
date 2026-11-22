-- 마산고 55회 졸업 30주년 기념행사 사진첩 일괄 등록 (37장)
-- Supabase SQL Editor 에 붙여 넣고 Run. 다시 실행해도 중복 등록되지 않는다.

alter table photos drop constraint if exists photos_event_check;
alter table photos add constraint photos_event_check check (event in ('수학여행','졸업식','수련회','체육대회','교실','졸업앨범','졸업 30주년','기타'));

create or replace function album_load(pw text) returns json
language plpgsql stable security definer set search_path = public, extensions as $$
begin
  if not album_check(pw) then raise exception 'wrong password' using errcode = '28000'; end if;
  return json_build_object(
    'roster',   coalesce((select json_agg(r order by r.id) from (select id, name, c3, portrait from roster) r), '[]'::json),
    'answers',  coalesce((select json_agg(a) from (select person_id, c1, c2 from answers) a), '[]'::json),
    'teachers', coalesce((select json_agg(t order by t.id) from (select id, name, role, subject, grade, class, portrait from teachers) t), '[]'::json),
    'photos',   coalesce((select json_agg(p order by array_position(array['졸업 30주년','수학여행','수련회','체육대회','교실','졸업앨범','졸업식','기타'], p.event), p.sort_order nulls last, p.created_at)
                          from (select id, path, ai_path, event, caption, contributor, sort_order, grade, created_at from photos where hidden = false) p), '[]'::json)
  );
end $$;

delete from photos where path like 'reunion30/%';
insert into photos (path, event, caption, sort_order) values
  ('reunion30/reunion30-01-s10.jpg', '졸업 30주년', '마산고 55회 졸업 30주년 기념행사 단체사진', 10),
  ('reunion30/reunion30-02-s20.jpg', '졸업 30주년', '1부 기념식 · 행사장 전경', 20),
  ('reunion30/reunion30-03-s21.jpg', '졸업 30주년', '1부 기념식 · 포토월', 21),
  ('reunion30/reunion30-04-s22.jpg', '졸업 30주년', '1부 기념식 · 축하 화환과 학년도기', 22),
  ('reunion30/reunion30-05-s23.jpg', '졸업 30주년', '1부 기념식 · 포토월 기념촬영', 23),
  ('reunion30/reunion30-06-s24.jpg', '졸업 30주년', '1부 기념식 · 반가운 얼굴들', 24),
  ('reunion30/reunion30-07-s30.jpg', '졸업 30주년', '1부 기념식 · 시상 및 선물 전달', 30),
  ('reunion30/reunion30-08-s31.jpg', '졸업 30주년', '1부 기념식 · 시상 및 선물 전달', 31),
  ('reunion30/reunion30-09-s32.jpg', '졸업 30주년', '1부 기념식 · 시상 및 선물 전달', 32),
  ('reunion30/reunion30-10-s33.jpg', '졸업 30주년', '1부 기념식 · 시상 및 선물 전달', 33),
  ('reunion30/reunion30-11-s34.jpg', '졸업 30주년', '1부 기념식 · 시상 및 선물 전달', 34),
  ('reunion30/reunion30-12-s35.jpg', '졸업 30주년', '1부 기념식 · 시상 및 선물 전달', 35),
  ('reunion30/reunion30-13-s36.jpg', '졸업 30주년', '1부 기념식 · 시상 및 선물 전달', 36),
  ('reunion30/reunion30-14-s37.jpg', '졸업 30주년', '1부 기념식 · 시상 및 선물 전달', 37),
  ('reunion30/reunion30-15-s40.jpg', '졸업 30주년', '1부 기념식 · 만찬장 풍경', 40),
  ('reunion30/reunion30-16-s41.jpg', '졸업 30주년', '1부 기념식 · 건배', 41),
  ('reunion30/reunion30-17-s42.jpg', '졸업 30주년', '1부 기념식 · 기념품과 함께', 42),
  ('reunion30/reunion30-18-s50.jpg', '졸업 30주년', '축하공연 · 무대 공연', 50),
  ('reunion30/reunion30-19-s51.jpg', '졸업 30주년', '축하공연 · 무대 공연', 51),
  ('reunion30/reunion30-20-s52.jpg', '졸업 30주년', '축하공연 · 피날레', 52),
  ('reunion30/reunion30-21-s53.jpg', '졸업 30주년', '축하공연 · 무대 앞 동문 환호', 53),
  ('reunion30/reunion30-22-s54.jpg', '졸업 30주년', '축하공연 · 동문 댄스 무대', 54),
  ('reunion30/reunion30-23-s55.jpg', '졸업 30주년', '축하공연 · 무대 앞 떼창과 호응', 55),
  ('reunion30/reunion30-24-s56.jpg', '졸업 30주년', '축하공연 · 무대 앞 호흡', 56),
  ('reunion30/reunion30-25-s57.jpg', '졸업 30주년', '축하공연 · 무대 인사', 57),
  ('reunion30/reunion30-26-s58.jpg', '졸업 30주년', '축하공연 · 테이블 앞 깜짝 무대', 58),
  ('reunion30/reunion30-27-s70.jpg', '졸업 30주년', '2차 뒤풀이 · 호프집 전경', 70),
  ('reunion30/reunion30-28-s71.jpg', '졸업 30주년', '2차 뒤풀이 · 테이블 인사', 71),
  ('reunion30/reunion30-29-s72.jpg', '졸업 30주년', '2차 뒤풀이 · 반가운 담소', 72),
  ('reunion30/reunion30-30-s73.jpg', '졸업 30주년', '2차 뒤풀이 · 테이블 정담', 73),
  ('reunion30/reunion30-31-s74.jpg', '졸업 30주년', '2차 뒤풀이 · 테이블 기념촬영', 74),
  ('reunion30/reunion30-32-s75.jpg', '졸업 30주년', '2차 뒤풀이 · 진한 우정', 75),
  ('reunion30/reunion30-33-s80.jpg', '졸업 30주년', '2차 뒤풀이 · 마무리 인사', 80),
  ('reunion30/reunion30-34-s81.jpg', '졸업 30주년', '2차 뒤풀이 · 아쉬운 작별', 81),
  ('reunion30/reunion30-35-s82.jpg', '졸업 30주년', '2차 뒤풀이 · 다음을 기약하며', 82),
  ('reunion30/reunion30-36-s83.jpg', '졸업 30주년', '2차 뒤풀이 · 엘리베이터 배웅', 83),
  ('reunion30/reunion30-37-s84.jpg', '졸업 30주년', '2차 뒤풀이 · 귀가길 브이', 84);

notify pgrst, 'reload schema';
