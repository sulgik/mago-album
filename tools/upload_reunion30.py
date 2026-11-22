"""졸업 30주년 기념행사 선별 사진(연사 중복 제거 37장)을 긴 변 2000px JPEG로 줄여
Supabase Storage 'photos' 버킷에 올리고, photos 표 등록용 SQL(또는 RPC 호출)을 수행한다.

사용법:
  1) Storage 업로드 + SQL 파일 생성 (비밀번호 불필요):
     python3 tools/upload_reunion30.py --sql > supabase/reunion30_photos.sql
     (생성된 SQL을 Supabase SQL Editor에서 실행하면 sort_order까지 한 번에 반영됨)

  2) 비밀번호로 RPC(album_add_photo)까지 바로 호출 (서버에 reunion30.sql 적용 후):
     ALBUM_PW="동문회비밀번호" python3 tools/upload_reunion30.py --rpc
"""
import argparse
import glob
import io
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from PIL import Image, ImageOps

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl.create_default_context()

SUPABASE_URL = "https://ofewlxuhmdlwdfshgdhr.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_qhB2fsugqAreLahFoAvgwg_HHqEdp0R"
DEFAULT_SRC_DIR = "/Users/sulgik/Downloads/졸업30주년_선별/사진"
STORAGE_PREFIX = "reunion30"
EVENT_NAME = "졸업 30주년"

# (파일 정렬 순번 1-based, sort_order, caption)
# 69장 중 1~3초 간격 중복 연사를 추리고 행사 시간순 + 대표 단체사진 맨 앞 배치로 큐레이션한 37장
CURATED = [
    # 대표 단체사진 (Hero: 갤러리 맨 위 전체 폭)
    (24, 10, "마산고 55회 졸업 30주년 기념행사 단체사진"),
    # 1부 기념식·만찬
    (65, 20, "1부 기념식 · 행사장 전경"),
    (67, 21, "1부 기념식 · 포토월"),
    (66, 22, "1부 기념식 · 축하 화환과 학년도기"),
    (68, 23, "1부 기념식 · 포토월 기념촬영"),
    (69, 24, "1부 기념식 · 반가운 얼굴들"),
    (2,  30, "1부 기념식 · 시상 및 선물 전달"),
    (4,  31, "1부 기념식 · 시상 및 선물 전달"),
    (6,  32, "1부 기념식 · 시상 및 선물 전달"),
    (7,  33, "1부 기념식 · 시상 및 선물 전달"),
    (8,  34, "1부 기념식 · 시상 및 선물 전달"),
    (10, 35, "1부 기념식 · 시상 및 선물 전달"),
    (11, 36, "1부 기념식 · 시상 및 선물 전달"),
    (13, 37, "1부 기념식 · 시상 및 선물 전달"),
    (17, 40, "1부 기념식 · 만찬장 풍경"),
    (44, 41, "1부 기념식 · 건배"),
    (45, 42, "1부 기념식 · 기념품과 함께"),
    # 축하공연·무대
    (18, 50, "축하공연 · 무대 공연"),
    (19, 51, "축하공연 · 무대 공연"),
    (27, 52, "축하공연 · 피날레"),
    (28, 53, "축하공연 · 무대 앞 동문 환호"),
    (31, 54, "축하공연 · 동문 댄스 무대"),
    (34, 55, "축하공연 · 무대 앞 떼창과 호응"),
    (38, 56, "축하공연 · 무대 앞 호흡"),
    (41, 57, "축하공연 · 무대 인사"),
    (64, 58, "축하공연 · 테이블 앞 깜짝 무대"),
    # 2차 뒤풀이
    (46, 70, "2차 뒤풀이 · 호프집 전경"),
    (47, 71, "2차 뒤풀이 · 테이블 인사"),
    (49, 72, "2차 뒤풀이 · 반가운 담소"),
    (50, 73, "2차 뒤풀이 · 테이블 정담"),
    (52, 74, "2차 뒤풀이 · 테이블 기념촬영"),
    (63, 75, "2차 뒤풀이 · 진한 우정"),
    (53, 80, "2차 뒤풀이 · 마무리 인사"),
    (54, 81, "2차 뒤풀이 · 아쉬운 작별"),
    (57, 82, "2차 뒤풀이 · 다음을 기약하며"),
    (58, 83, "2차 뒤풀이 · 엘리베이터 배웅"),
    (61, 84, "2차 뒤풀이 · 귀가길 브이"),
]


def shrink_image(path: str, max_side: int = 2000, quality: int = 85) -> bytes:
    im = ImageOps.exif_transpose(Image.open(path))
    if im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size
    if max(w, h) > max_side:
        k = max_side / max(w, h)
        im = im.resize((round(w * k), round(h * k)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def upload_to_storage(storage_path: str, data: bytes) -> None:
    url = f"{SUPABASE_URL}/storage/v1/object/photos/{storage_path}"
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "image/jpeg",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 400 and "Duplicate" in body:
            return
        raise RuntimeError(f"Storage upload failed ({e.code}) for {storage_path}: {body}") from e


def rpc_add_photo(pw: str, storage_path: str, event: str, caption: str) -> None:
    url = f"{SUPABASE_URL}/rest/v1/rpc/album_add_photo"
    payload = json.dumps({
        "pw": pw,
        "p_path": storage_path,
        "p_event": event,
        "p_caption": caption,
        "p_contributor": "",
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as resp:
        resp.read()


def q(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC_DIR, help="원본 사진 폴더 경로")
    ap.add_argument("--no-upload", action="store_true", help="Storage 업로드 건너뛰고 SQL만 출력")
    ap.add_argument("--rpc", action="store_true", help="ALBUM_PW 환경변수로 album_add_photo RPC 호출")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.src, "*")))
    if len(files) < 69:
        raise SystemExit(f"Expected 69 files in {args.src}, found {len(files)}")

    rows = []
    for seq, (idx, sort_order, caption) in enumerate(CURATED, start=1):
        src_file = files[idx - 1]
        storage_path = f"{STORAGE_PREFIX}/reunion30-{seq:02d}-s{sort_order:02d}.jpg"
        if not args.no_upload:
            jpg = shrink_image(src_file)
            upload_to_storage(storage_path, jpg)
            print(f"[{seq:02d}/{len(CURATED)}] uploaded {storage_path} ({len(jpg)//1024} KB) <- {os.path.basename(src_file)}", file=sys.stderr)
        rows.append((storage_path, EVENT_NAME, caption, sort_order))

    if args.rpc:
        pw = os.environ.get("ALBUM_PW", "").strip()
        if not pw:
            raise SystemExit("ALBUM_PW 환경변수가 필요합니다.")
        for storage_path, event, caption, _ in rows:
            rpc_add_photo(pw, storage_path, event, caption)
        print(f"RPC로 {len(rows)}장 등록 완료.", file=sys.stderr)

    # SQL 출력 (reunion30.sql 스키마 변경 + photos insert 한 번에 실행 가능)
    print("-- 마산고 55회 졸업 30주년 기념행사 사진첩 일괄 등록 (37장)")
    print("-- Supabase SQL Editor 에 붙여 넣고 Run. 다시 실행해도 중복 등록되지 않는다.\n")
    print("alter table photos drop constraint if exists photos_event_check;")
    print("alter table photos add constraint photos_event_check check (event in ('수학여행','졸업식','수련회','체육대회','교실','졸업앨범','졸업 30주년','기타'));\n")
    print("""create or replace function album_load(pw text) returns json
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
""")
    print("delete from photos where path like 'reunion30/%';")
    print("insert into photos (path, event, caption, sort_order) values")
    print(",\n".join(f"  ({q(p)}, {q(ev)}, {q(cap)}, {so})" for p, ev, cap, so in rows) + ";")
    print("\nnotify pgrst, 'reload schema';")


if __name__ == "__main__":
    main()
