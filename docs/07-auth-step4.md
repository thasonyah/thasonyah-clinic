# ขั้น 4 — Authentication และสิทธิ์

วันที่ 12 กันยายน 2569 สถานะ: backend พร้อมตรวจในเครื่อง; ยังไม่ deploy และยังไม่ต่อหน้าล็อกอินจริง

## API ที่ทำแล้ว

- POST /api/v1/auth/login — JSON email/password; bcrypt; JWT HS256 อายุเริ่มต้น 30 นาที; จำกัด 10 ครั้ง/นาทีต่อ IP; ไม่มี public registration
- GET /api/v1/auth/me — identity และ permissions ไม่มี hash
- POST /api/v1/auth/logout — revoke session ใน PostgreSQL; token เดิมใช้ซ้ำไม่ได้
- POST /api/v1/auth/change-password — ตรวจรหัสปัจจุบัน; ยกเลิกทุก session รวมปัจจุบัน ต้อง login ใหม่
- GET /api/v1/users?limit=25&offset=0 — admin เท่านั้น
- POST /api/v1/users — admin เท่านั้น; email, password, role; ไม่ส่งรหัสหรือ hash กลับ
- validation errors ไม่สะท้อน input เพื่อไม่เปิดเผยรหัสผ่าน

## สิทธิ์ขั้นต้น

| Role | สิทธิ์ |
|---|---|
| admin | users.manage, clinic.read, clinic.manage |
| manager | clinic.read, reports.read |
| practitioner | clinic.read, clinical.read/write/sign |
| reception | clinic.read, patients.read/create, scheduling.write |
| finance | clinic.read, billing.read/write |
| pharmacy | clinic.read, dispensing.read/write |

ตรวจ JWT และ session ที่ยังใช้งาน พร้อมสถานะ user active จากฐานข้อมูลทุก request ผ่าน deps.py จึงไม่เชื่อ role ที่ client ส่งมา แอดมินไม่มี clinical.read โดยอัตโนมัติ สิทธิ์โมดูลที่ยังไม่สร้างเป็น permission vocabulary สำหรับขั้น 5 ไม่ใช่หลักฐานว่าโมดูลนั้นพร้อมแล้ว

## ตั้งค่าและสร้างผู้ดูแลคนแรก

1. ตั้ง DATABASE_URL และ JWT_SECRET ใน .env ตาม README และเปิด PostgreSQL
2. ใน backend รัน `.venv/bin/python -m alembic upgrade head`
3. ตั้ง BOOTSTRAP_ADMIN_EMAIL และ BOOTSTRAP_ADMIN_PASSWORD ผ่าน environment/config; รหัสอย่างน้อย 12 ตัวอักษร ไม่เกิน 72 UTF-8 bytes
4. รัน `.venv/bin/python -m scripts.bootstrap_admin` แล้วลบค่า bootstrap ออกจาก environment

สคริปต์ไม่แก้บัญชีเดิมและปฏิเสธเมื่อมี active admin อยู่แล้ว ไม่สร้างบัญชีจากรหัสผ่านที่เคยส่งในแชต ไม่มีบัญชีทดลองเปิดเผยในขั้นนี้

## ผลทดสอบ

PostgreSQL 15 แยกฐาน clinic_auth_test; migration 0002_identity; 7 tests ผ่าน coverage app รวม 97% (เฉพาะโค้ดที่มี ไม่ใช่ทั้งโครงการ)

- ไม่มี token / token ผิด → 401
- ผู้ไม่มีสิทธิ์ทั้ง 5 บทบาท → 403 ทั้งอ่านและสร้างบัญชี
- admin อ่าน/สร้างได้และไม่มี hash รั่ว; ชื่อบัญชีซ้ำ → 409
- logout / password change / disabled user / expired DB session → 401
- login เกิน 10 ครั้ง/นาที → 429
- ข้อมูล validation ไม่สะท้อนรหัสผ่าน
- ปิด permission check ชั่วคราวแล้วเทสล้มจริง; คืนโค้ดแล้วรันผ่าน

หลักฐาน: docs/evidence/step4-red.txt, step4-red-validation.txt, step4-red-permission.txt, step4-green.txt

## ขอบเขตที่ยังไม่ทำ

- หน้าเข้าสู่ระบบและ frontend guard/API integration อยู่ขั้น 6; /design เป็นต้นแบบสาธิตเท่านั้น
- สาขา/assignment/สิทธิ์ระดับรายการ ต้องตรวจเพิ่มใน endpoint โมดูลขั้น 5 ก่อนใช้ข้อมูลคนไข้
- การแก้ role/ปิดบัญชีผ่าน admin UI, ป้องกันถอนแอดมินคนสุดท้าย, audit log บัญชี และ password recovery ยังเป็นงานต่อยอด; ไม่เปิด endpoint เปลี่ยน role ที่ไม่สมบูรณ์
- GET users ใช้ limit/offset ชั่วคราว ไม่ใช่ cursor envelope ตาม design contract; ต้องปรับพร้อม frontend
- ยังไม่มี GitHub remote/PR/CI online และ Render; ผลนี้เป็น local verification เท่านั้น
- มี deprecation warnings ของ testclient/httpx/passlib แต่ไม่เปลี่ยน stack ที่ผู้ใช้กำหนด
