# Seed — thành viên 3

Chỉ dữ liệu demo giả lập, không dữ liệu cá nhân thật và không password hash dùng lại giữa các môi trường. Tạo teacher bằng python -m server.app.seed; không thêm tài khoản mặc định có mật khẩu cố định. Migration đặt tại database/migrations/versions/, cùng một chuỗi revision với 0001_auth.

# D02 — Du lieu demo LAN-LMS (chi dung cuc bo)

Script `database/seed/seed_demo.py` tao du lieu demo LMS: 1 ho so giang vien, 3 sinh vien, 2 lop, 1 hoc phan, va cac quan he. Script **khong** tao mat khau mac dinh cho giang vien; giu nguyen `server/app/seed.py` cua TV1.

## Chuan bi

Chay tu thu muc goc repository, sau khi kich hoat `.venv` va cai dependencies:

```powershell
python -m alembic -c server/alembic.ini upgrade head
python -m alembic -c server/alembic.ini current
```

Ket qua mong doi: `0002_database_base (head)`. Chi chay voi database **local/demo**, khong chay voi database that.

## Tao tai khoan giang vien (neu chua co)

```powershell
python -m server.app.seed
```

Nhap username (vi du `demo_teacher`) va mat khau tu ban phim. Khong commit mat khau vao repository.

## Seed du lieu LMS

```powershell
python -m database.seed.seed_demo --teacher-username demo_teacher
```

Thay `demo_teacher` bang username giang vien da tao. Lan dau script se hoi mat khau cho 3 tai khoan sinh vien demo; cac lan chay sau se tai su dung ban ghi da ton tai. Script khong xoa/ghi de ban ghi co san.

Du lieu demo:

| Loai       | Ma / username                                                                      |
| ---------- | ---------------------------------------------------------------------------------- |
| Giang vien | `DEMO-GV001` (ho so cua tai khoan giang vien duoc chon)                            |
| Sinh vien  | `demo_sv01` / `DEMO-SV001`; `demo_sv02` / `DEMO-SV002`; `demo_sv03` / `DEMO-SV003` |
| Lop        | `DEMO-CNTT01`, `DEMO-CNTT02`                                                       |
| Hoc phan   | `DEMO-LTM`, hoc ky `1`, nam hoc `2026-2027`                                        |
| Quan he    | 1 phan cong giang vien, 2 lien ket lop-hoc phan, 3 dang ky hoc phan                |

## Kiem tra

Chay lai lenh seed: cac ban ghi da ton tai se in `Exists`, ket thuc bang `D02 demo seed completed successfully.`

Kiem tra khoa ngoai:

```powershell
@'
from sqlalchemy import text
from server.app.core.config import Settings
from server.app.core.database import database
engine, _ = database(Settings().database_url)
with engine.connect() as conn:
    violations = conn.execute(text("PRAGMA foreign_key_check")).fetchall()
    print("PASSED: No foreign key violations" if not violations else violations)
engine.dispose()
'@ | python -
```

## An toan va pham vi

- Khong commit `.venv`, `server/.env`, `database/lan_lms.db` hoac mat khau demo.
- Script phu thuoc cac model D01 va `User`/`hasher` cua TV1.
- Gia tri demo `status=active`, `role=primary`, `final_grade_policy=highest_published_final_exam` can duoc nhom xac nhan truoc khi dung cho logic nghiep vu chinh thuc.
- Chi danh cho moi truong phat trien/kiem thu; khong chay voi database production.
