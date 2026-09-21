# ขั้นที่ 3 — โครงโปรเจกต์และ CI

สถานะ: โครงและการตรวจในเครื่องเสร็จแล้ว; ขั้นที่ 3 ยังรอ GitHub repository/PR/CI/branch protection

## สิ่งที่สร้าง

- backend ตาม stack และ folder structure เดิม; public health/readiness เท่านั้น ยังไม่มี auth/ข้อมูลคนไข้
- SQLAlchemy/PostgreSQL, Alembic baseline ว่าง, config จาก env, seed entry point ที่แจ้งว่ายังไม่สร้างข้อมูล
- React 18/Vite 5/Tailwind 3, Router, axios client, หน้าแจ้งว่ายังไม่เปิดบริการ
- Compose PostgreSQL 15, GitHub Actions 2 jobs และ Blueprint Render 3 resources
- .env.example, .gitignore, MIT LICENSE และ README สำหรับ local dev
- root commit บน main มีเพียงโครงเปล่าและ .gitignore; งานจริงอยู่ codex/project-scaffold

## สถานะภายนอก

GitHub connector ที่เชื่อมอยู่คือ catsthailand; เครื่องยังไม่มี gh CLI; ไม่ได้สร้าง repo, push, PR หรือเปิด branch protection เพราะยังไม่ทราบชื่อ repository ที่ผู้ใช้ต้องการ

ยังไม่ได้ deploy หรือสร้าง resource บน Render ชื่อ clinic-api/clinic-web/clinic-db ใน Blueprint เป็นชื่อเสนอสำหรับ demo เท่านั้น

## Dependency audit

อัปเดต React Router, recharts และ vitest ภายในเทคโนโลยีเดิมแล้ว เพื่อลด advisory จากเวอร์ชันเริ่มต้น แต่ npm audit ยังรายงาน 4 รายการ (3 moderate, 1 high) ในสาย Vite 5 และเครื่องมือทดสอบ การแก้ที่ npm เสนอเปลี่ยน Vite major จึงยังไม่ทำโดยพลการตามข้อห้ามเปลี่ยน stack ต้องทบทวนก่อนใช้งานจริง ห้ามเปิด dev server สู่สาธารณะ

## ลำดับที่เหลือ

ขั้น 3 ยังค้าง GitHub repository/PR/required CI/branch protection เมื่อครบขั้นนี้เหลือ 5 ขั้น:
4. Auth + สิทธิ์ + tests 403
5. ฟีเจอร์ทีละ branch/PR พร้อม tests
6. Seed สมมติและหน้าจอครบ
7. Deploy Render และทดสอบ production
8. เอกสาร/README/หลักฐานฉบับส่งมอบ

P1–P4 ใน requirements เป็นเฟสของฟีเจอร์ ไม่ใช่ขั้น 1–8 ของกระบวนการ จึงไม่ควรนำจำนวนเฟสมาบวกจำนวนขั้น

## ผลตรวจจริงในเครื่อง

- Python 3.11.14 (Render ยังคงตรึง 3.11.9): ruff ผ่าน
- PostgreSQL 15 ใน Docker แยก project clinic-scaffold-test: Alembic baseline upgrade ผ่าน
- pytest: 3 passed, scaffold coverage 95% (ไม่ใช่ coverage ของฟีเจอร์ที่ยังไม่ได้สร้าง)
- Red check 1: ปิด validator บังคับ PostgreSQL ชั่วคราว → test_rejects_non_postgres ล้มจริง; คืนโค้ดแล้วผ่าน
- Red check 2: เปลี่ยน health status เป็นค่าผิดชั่วคราว → integration health contract ล้มจริง; คืนโค้ดแล้วผ่าน
- React production build ผ่านด้วย Node 20 และ Vite 5.4.21
- vitest runner รันได้ แต่ยังไม่มี frontend test cases ในขั้น scaffold
- render.yaml ผ่าน JSON Schema draft 2020-12 จาก Render; ไม่ใช่หลักฐานว่า deploy สำเร็จ
- git diff --check ผ่าน; reference PDFs/images และไฟล์ตั้งค่าลับไม่อยู่ในรายการ commit

Dependency หลักของ backend ตรึงตามชุดที่ติดตั้งทดสอบแล้ว; frontend มี package-lock.json
