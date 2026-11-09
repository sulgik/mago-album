"""졸업앨범에서 옮긴 명단 CSV(이름,3학년반[,번호]) → Supabase SQL insert 문.

사용: python3 roster_to_sql.py roster.csv > roster.sql
그다음 roster.sql 내용을 Supabase SQL Editor 에 붙여 넣고 Run.
같은 id 가 이미 있으면 이름·반을 덮어쓴다.
"""
import csv
import sys


def q(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def main(path: str) -> None:
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for i, r in enumerate(csv.reader(f)):
            if not r or not r[0].strip():
                continue
            if i == 0 and r[0].strip() in ("이름", "name"):
                continue
            name = r[0].strip()
            c3 = int(r[1]) if len(r) > 1 and r[1].strip() else None
            no = r[2].strip() if len(r) > 2 and r[2].strip() else str(len(rows) + 1)
            pid = f"3-{c3 or 0:02d}-{int(no):02d}" if no.isdigit() else f"3-{c3 or 0:02d}-{no}"
            rows.append((pid, name, c3))
    print("insert into roster (id, name, c3) values")
    print(",\n".join(f"  ({q(p)}, {q(n)}, {c if c else 'null'})" for p, n, c in rows))
    print("on conflict (id) do update set name = excluded.name, c3 = excluded.c3;")
    print(f"-- {len(rows)}명", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
