# 마산고 온라인 앨범 — 설치 안내

이름 검색(1·2·3학년 반), 반별 명단, 사진첩(수학여행·졸업식 등).
화면은 GitHub Pages(무료), 데이터와 사진은 Supabase(무료 등급)에 둔다.
링크만 있으면 누구나 보고 입력할 수 있다(로그인 없음). 검색엔진 노출은 막아 두었다.

## 구조

| 파일 | 역할 |
|---|---|
| `index.html` | 사이트 전체 |
| `config.js` | Supabase 주소·공개키. 비우면 예시 데이터로 도는 데모 모드 |
| `supabase/schema.sql` | 표·접근 규칙·사진 버킷 생성 |
| `supabase/password.sql` | 공유 비밀번호 잠금. 표 직접 읽기를 막고 `album_*` 함수로만 읽고 쓴다 |
| `supabase/contributor.sql` | 사진첩에 "사진 주인(제공자)" 칸 추가. 이미 운영 중인 서버에서 한 번 실행 |
| `supabase/order.sql` | 사진첩 나열 순서(행사 순서 → 순서 번호 → 올린 순서)와 행사 분류 '졸업앨범'. `contributor.sql` 다음에 한 번 실행 |
| `supabase/grade.sql` | 사진에 학년 칸 추가. 학년을 아는 사진(수학여행 = 2학년)은 사진 주인의 그 학년 반 화면에도 나온다. `order.sql` 다음에 한 번 실행 |
| `tools/roster_to_sql.py` | 명단 CSV → 넣기용 SQL |

데이터 규칙:
- `roster` (이름, 3학년 반): 사이트에서는 못 바꾼다. 운영진이 SQL 로만 넣는다.
- `answers` (1·2학년 반): 누구나 입력·수정. 모든 변경이 `answers_log` 에 남아 되돌릴 수 있다.
- `photos`: 누구나 올린다. 올릴 때 "사진 주인 이름"을 적으면 사진첩이 사진 주인별로 나뉜다(같은 행사라도 사진 주인마다 반이 달라서).
  이름이 명단에 한 명뿐이면 그 사람의 반도 함께 보여 준다. 사진은 긴 변 2000px JPEG 로 줄여 올라간다(장당 약 0.3~1MB, 5MB 상한).
  지우거나 숨기려면 대시보드에서 해당 행의 `hidden` 을 true 로.
  행사 분류가 '졸업앨범'인 사진(졸업앨범 책에서 옮긴 반 단체·교실·조별 사진)은 사진첩이 아니라 졸업앨범 탭의 3학년 반별 화면에 나온다.
  어느 반인지는 설명 맨 앞의 `3학년 N반` 으로 읽고, 설명에 `단체` 가 있으면 반 맨 위에 크게 나온다. 사이트의 올리기 목록에는 이 분류가 없다(운영진이 넣는다).

## 1. Supabase 프로젝트 만들기 (운영진이 직접)

1. https://supabase.com 가입 → New project (지역: Northeast Asia (Seoul))
2. SQL Editor → `supabase/schema.sql` 내용 붙여 넣고 Run, 이어서 `supabase/password.sql` 도 Run
   - 비밀번호 정하기: `password.sql` 안의 주석대로 `insert into album_settings ...` 를 실제 비밀번호로 바꿔 한 번 실행
   - 비밀번호를 바꾸면 모든 동문이 다시 입력해야 한다
3. Project Settings → API 에서 `Project URL` 과 `anon public` 키를 `config.js` 에 넣는다
   - `service_role` 키는 절대 넣지 않는다

무료 등급: DB 500MB, 사진 저장 1GB(줄인 사진 기준 약 1,500~3,000장).
1주일간 접속이 없으면 프로젝트가 일시정지되니, 행사 전후로 한 번씩 열어 본다.

## 2. 명단 넣기

졸업앨범에서 옮긴 CSV (`이름,3학년반,번호`):

```bash
python3 tools/roster_to_sql.py roster.csv > roster.sql
```

`roster.sql` 내용을 SQL Editor 에 붙여 넣고 Run. 다시 넣으면 덮어쓴다.

## 3. GitHub Pages 게시

이 `site/` 폴더 내용을 공개 저장소에 올리고 Settings → Pages → `main` / root.
주소 예: `https://<계정>.github.io/masanhs-album/`

## 장난 입력 되돌리기

```sql
-- 특정 사람의 변경 이력
select * from answers_log where person_id = '3-02-01' order by at desc;
```
