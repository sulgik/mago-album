"""졸업 30주년 기념행사 선별 사진(연사 중복 제거 42장)을 긴 변 2000px JPEG로 줄여
Supabase Storage 'photos' 버킷에 올리고, photos 표 등록용 SQL(또는 RPC 호출)을 수행한다.

사용법:
  1) Storage 업로드 + SQL 파일 생성 (비밀번호 불필요):
     python3 tools/upload_reunion30.py > supabase/reunion30.sql
     (생성된 SQL을 Supabase SQL Editor에서 실행하면 sort_order까지 한 번에 반영됨)

  2) 신규 추가분만 Storage 업로드:
     python3 tools/upload_reunion30.py --only-new > supabase/reunion30.sql
"""
import argparse
import io
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
import cv2
import numpy as np
from PIL import Image, ImageOps

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl.create_default_context()

SUPABASE_URL = "https://ofewlxuhmdlwdfshgdhr.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_qhB2fsugqAreLahFoAvgwg_HHqEdp0R"
DEFAULT_SRC_DIR = "/Volumes/Blue/마고55_졸업30주년/졸업30주년_선별/사진"
STORAGE_PREFIX = "reunion30_v2"
EVENT_NAME = "졸업 30주년"

# (storage_filename, source_filename, sort_order, caption)
CURATED = [
    # 대표 단체사진 (Hero: 갤러리 맨 위 전체 폭)
    ("reunion30-01-s10.jpg", "1795326227179.jpg", 10, "마산고 55회 졸업 30주년 기념행사 단체사진"),
    # 1부 기념식·만찬
    ("reunion30-02-s20.jpg", "KakaoTalk_Photo_2026-11-22-19-32-07 001.jpeg", 20, "1부 기념식 · 행사장 전경"),
    ("reunion30-03-s21.jpg", "KakaoTalk_Photo_2026-11-22-19-32-08 003.jpeg", 21, "1부 기념식 · 포토월"),
    ("reunion30-04-s22.jpg", "KakaoTalk_Photo_2026-11-22-19-32-07 002.jpeg", 22, "1부 기념식 · 축하 화환과 학년도기"),
    ("reunion30-05-s23.jpg", "KakaoTalk_Photo_2026-11-22-19-32-08 004.jpeg", 23, "1부 기념식 · 포토월 기념촬영"),
    ("reunion30-06-s24.jpg", "KakaoTalk_Photo_2026-11-22-19-32-51.jpeg", 24, "1부 기념식 · 반가운 얼굴들"),
    ("reunion30-38-s25.jpg", "IMG_2326.jpeg", 25, "1부 기념식 · 기념촬영"),
    ("reunion30-07-s30.jpg", "1795326220153.jpg", 30, "1부 기념식 · 시상 및 선물 전달"),
    ("reunion30-08-s31.jpg", "1795326220355.jpg", 31, "1부 기념식 · 시상 및 선물 전달"),
    ("reunion30-09-s32.jpg", "1795326220558.jpg", 32, "1부 기념식 · 시상 및 선물 전달"),
    ("reunion30-10-s33.jpg", "1795326220662.jpg", 33, "1부 기념식 · 시상 및 선물 전달"),
    ("reunion30-11-s34.jpg", "1795326221065.jpg", 34, "1부 기념식 · 시상 및 선물 전달"),
    ("reunion30-12-s35.jpg", "1795326221266.jpg", 35, "1부 기념식 · 시상 및 선물 전달"),
    ("reunion30-13-s36.jpg", "1795326221364.jpg", 36, "1부 기념식 · 시상 및 선물 전달"),
    ("reunion30-14-s37.jpg", "1795326221557.jpg", 37, "1부 기념식 · 시상 및 선물 전달"),
    ("reunion30-15-s40.jpg", "1795326226662.jpg", 40, "1부 기념식 · 만찬장 풍경"),
    ("reunion30-16-s41.jpg", "1795326229240.jpg", 41, "1부 기념식 · 건배"),
    ("reunion30-17-s42.jpg", "1795326234856.jpg", 42, "1부 기념식 · 기념품과 함께"),
    # 축하공연·무대 (1부 기념식에 통합)
    ("reunion30-18-s50.jpg", "1795326226702.jpg", 50, "1부 기념식 · 무대 공연"),
    ("reunion30-19-s51.jpg", "1795326226770.jpg", 51, "1부 기념식 · 무대 공연"),
    ("reunion30-20-s52.jpg", "1795326227551.jpg", 52, "1부 기념식 · 피날레"),
    ("reunion30-21-s53.jpg", "1795326227644.jpg", 53, "1부 기념식 · 무대 앞 동문 환호"),
    ("reunion30-22-s54.jpg", "1795326227956.jpg", 54, "1부 기념식 · 동문 댄스 무대"),
    ("reunion30-23-s55.jpg", "1795326228242.jpg", 55, "1부 기념식 · 무대 앞 떼창과 호응"),
    ("reunion30-24-s56.jpg", "1795326228647.jpg", 56, "1부 기념식 · 무대 앞 호흡"),
    ("reunion30-25-s57.jpg", "1795326228942.jpg", 57, "1부 기념식 · 무대 인사"),
    ("reunion30-26-s58.jpg", "KakaoTalk_Photo_2026-11-22-19-29-10.jpeg", 58, "1부 기념식 · 테이블 앞 깜짝 무대"),
    # 2차 뒤풀이
    ("reunion30-27-s70.jpg", "1795326234943.jpg", 70, "2차 뒤풀이 · 호프집 전경"),
    ("reunion30-28-s71.jpg", "1795326234974.jpg", 71, "2차 뒤풀이 · 테이블 인사"),
    ("reunion30-39-s71.jpg", "IMG_2333.jpeg", 71, "2차 뒤풀이 · 테이블 정담"),
    ("reunion30-29-s72.jpg", "1795326235050.jpg", 72, "2차 뒤풀이 · 반가운 담소"),
    ("reunion30-30-s73.jpg", "1795326235079.jpg", 73, "2차 뒤풀이 · 테이블 정담"),
    ("reunion30-31-s74.jpg", "1795326235138.jpg", 74, "2차 뒤풀이 · 테이블 기념촬영"),
    ("reunion30-32-s75.jpg", "KakaoTalk_Photo_2026-11-22-19-28-57.jpeg", 75, "2차 뒤풀이 · 진한 우정"),
    ("reunion30-40-s76.jpg", "IMG_2336.jpeg", 76, "2차 뒤풀이 · 어깨동무"),
    ("reunion30-41-s77.jpg", "IMG_2339.jpeg", 77, "2차 뒤풀이 · 반가운 친구들"),
    ("reunion30-42-s78.jpg", "IMG_2340.jpeg", 78, "2차 뒤풀이 · 손하트"),
    ("reunion30-33-s80.jpg", "1795326235171.jpg", 80, "2차 뒤풀이 · 마무리 인사"),
    ("reunion30-34-s81.jpg", "1795326235214.jpg", 81, "2차 뒤풀이 · 아쉬운 작별"),
    ("reunion30-35-s82.jpg", "1795326235379.jpg", 82, "2차 뒤풀이 · 다음을 기약하며"),
    ("reunion30-36-s83.jpg", "1795326235425.jpg", 83, "2차 뒤풀이 · 엘리베이터 배웅"),
]


def enhance_photo(pil_im: Image.Image) -> Image.Image:
    """실내 조명 플레어(뿌연 안개감), 어두운 암부(2차 호프집), 노란 조명 색감 자동 보정."""
    rgb = np.asarray(pil_im, dtype=np.uint8)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    # 1. 암부 밝히기 전 컬러 노이즈 살짝 억제
    bgr = cv2.bilateralFilter(bgr, d=5, sigmaColor=18, sigmaSpace=18)

    # 2. 무대 스포트라이트 역광으로 뜬 블랙 레벨(Dehaze) 및 화이트 포인트 정렬
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    lf = l.astype(np.float32)
    p3, p50, p96 = np.percentile(lf, [3, 50, 96])

    black_floor = max(0.0, min(p3 - 10.0, 32.0)) * 0.65
    white_ceil = max(225.0, min(p96 + 15.0, 252.0))
    lf = np.clip((lf - black_floor) * (255.0 / max(white_ceil - black_floor, 120.0)), 0, 255)

    # 3. 어두운 사진(2차 호프집 등) 암부·중간톤 적응형 밝기 보정 (하이라이트 보호)
    p50_new = float(np.percentile(lf, 50))
    target_p50 = np.clip(p50_new * 0.55 + 52.0, 78.0, 122.0)
    gamma = np.log(target_p50 / 255.0) / np.log(max(p50_new, 15.0) / 255.0)
    gamma = float(np.clip(gamma, 0.68, 0.96))
    norm = lf / 255.0
    lifted = np.power(norm, gamma)
    blend_w = np.clip(1.0 - np.maximum(0.0, (norm - 0.65) / 0.35), 0.0, 1.0)
    norm = norm * (1.0 - blend_w) + lifted * blend_w
    l_u8 = np.clip(norm * 255.0, 0, 255).astype(np.uint8)

    # 4. 로컬 대비(CLAHE)로 인물 표정 또렷하게
    clahe = cv2.createCLAHE(clipLimit=1.35, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l_u8)
    l_final = cv2.addWeighted(l_u8, 0.55, l_clahe, 0.45, 0)

    # 5. 실내 황색/주황색 조명 캐스트 완화 및 자연스러운 생동감(Vibrance)
    af = a.astype(np.float32) - 128.0
    bf = b.astype(np.float32) - 128.0
    mean_a, mean_b = float(af.mean()), float(bf.mean())
    if mean_b > 5.0:
        bf -= min(mean_b - 5.0, 9.0) * 0.55
    if mean_a > 4.0:
        af -= min(mean_a - 4.0, 6.0) * 0.40
    af = np.clip(af * 1.05 + 128.0, 0, 255).astype(np.uint8)
    bf = np.clip(bf * 1.04 + 128.0, 0, 255).astype(np.uint8)

    lab_out = cv2.merge([l_final, af, bf])
    rgb_out = cv2.cvtColor(lab_out, cv2.COLOR_LAB2RGB)

    # 6. 미세 선명도(Unsharp Mask)
    blur = cv2.GaussianBlur(rgb_out, (0, 0), sigmaX=1.2)
    sharp = cv2.addWeighted(rgb_out, 1.18, blur, -0.18, 0)
    return Image.fromarray(sharp)


def shrink_image(path: str, max_side: int = 2000, quality: int = 87, enhance: bool = True) -> bytes:
    im = ImageOps.exif_transpose(Image.open(path))
    if im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size
    if max(w, h) > max_side:
        k = max_side / max(w, h)
        im = im.resize((round(w * k), round(h * k)), Image.Resampling.LANCZOS)
    if enhance:
        im = enhance_photo(im)
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
        if e.code == 400 and ("Duplicate" in body or "already exists" in body):
            return
        raise RuntimeError(f"Storage upload failed ({e.code}) for {storage_path}: {body}") from e


def q(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC_DIR, help="원본 사진 폴더 경로")
    ap.add_argument("--no-upload", action="store_true", help="Storage 업로드 건너뛰고 SQL만 출력")
    ap.add_argument("--only-new", action="store_true", help="신규 추가된 IMG_23*.jpeg 파일만 Storage에 업로드")
    args = ap.parse_args()

    rows = []
    for seq, (storage_name, src_name, sort_order, caption) in enumerate(CURATED, start=1):
        src_file = os.path.join(args.src, src_name)
        if not os.path.exists(src_file):
            raise SystemExit(f"Missing file: {src_file}")
        storage_path = f"{STORAGE_PREFIX}/{storage_name}"
        if not args.no_upload and (not args.only_new or src_name.startswith("IMG_23")):
            jpg = shrink_image(src_file)
            upload_to_storage(storage_path, jpg)
            print(f"[{seq:02d}/{len(CURATED)}] uploaded {storage_path} ({len(jpg)//1024} KB) <- {src_name}", file=sys.stderr)
        rows.append((storage_path, EVENT_NAME, caption, sort_order))

    print(f"-- 마산고 55회 졸업 30주년 기념행사 사진첩 일괄 등록 ({len(rows)}장)")
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
    print("delete from photos where path like 'reunion30/%' or path like 'reunion30_v2/%';")
    print("insert into photos (path, event, caption, sort_order) values")
    print(",\n".join(f"  ({q(p)}, {q(ev)}, {q(cap)}, {so})" for p, ev, cap, so in rows) + ";")
    print("\nnotify pgrst, 'reload schema';")


if __name__ == "__main__":
    main()
