// Supabase 프로젝트 설정. 대시보드 > Project Settings > API 에서 복사.
// 둘 다 비워 두면 예시 데이터로 도는 데모 모드가 된다.
// anon(public) 키는 공개돼도 되는 키다. service_role 키는 절대 넣지 말 것.
window.ALBUM_CONFIG = {
  SUPABASE_URL: "https://ofewlxuhmdlwdfshgdhr.supabase.co",
  SUPABASE_ANON_KEY: "sb_publishable_qhB2fsugqAreLahFoAvgwg_HHqEdp0R",   // publishable(공개) 키
  SCHOOL: "마산고등학교",
  CLASS_OF: "55기",      // 상단에 "마산고등학교 55기 동문회"로 표시
  MAX_CLASS: 12,         // 반 선택 목록의 최대 반 수
  YEARS: { 1: 1993, 2: 1994, 3: 1995 }   // 학년별 연도
};
