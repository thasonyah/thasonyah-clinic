# ฟังก์ชันหัตถการถาวร — 12 กันยายน 2569

## สิ่งที่เพิ่ม

- Migration 0003_catalog: PostgreSQL clinic_services ราคา Numeric(12,2), active, version
- GET /services ต้อง clinic.read; POST/PATCH ต้อง clinic.manage
- PATCH ส่ง expected_version ใช้ conditional UPDATE; ไม่ SELECT แล้วเขียนทับ
- seed หัตถการจริง 12 รายการจาก snapshot ที่ผู้ใช้ให้ (scripts/service_seed.json) รันซ้ำไม่ทับข้อมูล
- /staff: หน้าล็อกอินจริงและจัดการหัตถการผ่าน axios กลาง; read-only role ไม่มีปุ่มแก้ไข
- token อยู่ใน memory เท่านั้น รีโหลดให้ login ใหม่; รายการหัตถการอยู่ใน PostgreSQL
- /design/* ยังเป็นต้นแบบแยกต่างหาก

## ทดสอบ

pytest รวม 8 tests ผ่าน coverage โค้ดปัจจุบัน 96%; รวม 403 และการแข่งขัน 10 threads แก้ version เดียวกันสำเร็จ 1 อีก 9 ได้ 409
Red ก่อนประกอบ router ได้ 404 ไม่ผ่าน 403 assertion ตามคาด; หลักฐาน docs/evidence/step5-services-red.txt และ step5-services-green.txt
Build frontend ผ่าน; detector ไม่มี findings

## Local runtime

สร้างฐาน clinic_local แยกจาก clinic_auth_test ใน container clinic-auth-step4-test; ค่าลับอยู่ .env ที่ gitignore และ permission 600 ไม่ใช่ฐาน production
Backend: ใน backend รัน `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
Frontend: ใน frontend รัน `npm run dev -- --host 127.0.0.1 --port 5173`
Migration: `python -m alembic upgrade head`; Seed: `python -m scripts.seed`
ตั้งบัญชีแรกตาม docs/07-auth-step4.md ไม่ใช้บัญชีทดสอบ UI เป็นบัญชีคลินิก

## งานที่ยังไม่เสร็จทั้งโครงการ

ทะเบียน/OPD แบบถาวร, สิทธิ์สาขา/assignment, นัดหมาย/คิว/เตียง, ใบสั่งยาและคลัง, การเงิน/รายงาน, ลายเซ็นและ audit, จันทรคติ/จักรราศีที่ตรวจรับ, frontend ครบทุกโมดูล, GitHub PR/CI/protection, Render deploy, acceptance และเอกสารส่งมอบ

Catalog ยังต้องเพิ่ม audit log และการเก็บ snapshot ที่รายการรักษา/ใบเสร็จเมื่อทำโมดูลเหล่านั้น ไม่กล่าวว่าทั้งระบบคลินิกพร้อมใช้งาน
