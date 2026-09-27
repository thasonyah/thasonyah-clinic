# ระบบคลินิกแพทย์แผนไทย

ระบบบริหารคลินิกแพทย์แผนไทยสำหรับธสัญญา คลินิกการแพทย์แผนไทย มี public landing/booking, staff workspace, authentication, ทะเบียนคนไข้, OPD, นัดหมาย, หัตถการ, คลังยา, การเงิน, reset password และ workflow จักรราศี/ธาตุพื้นฐานตามข้อมูลวันเกิด

## Live Deployment

- Frontend: https://clinic-web-3z3c.onrender.com/
- Backend API: https://clinic-api-rl26.onrender.com/api/v1
- API readiness: https://clinic-api-rl26.onrender.com/api/v1/readyz
- Repository: https://github.com/thasonyah/thasonyah-clinic

สถานะ production ล่าสุด: frontend และ backend deploy จาก commit `401f9cc` แล้ว ตรวจ API readiness ผ่าน และ bundle frontend production มี flow สร้างนัดจากคำขอจองหน้าเว็บ

## Tech Stack

Python 3.11 / FastAPI / SQLAlchemy 2 / Alembic / Pydantic v2 / PostgreSQL 15 / python-jose / passlib / bcrypt 4.0.1 / slowapi / pytest / httpx / pytest-cov / ruff

React 18 / Vite / Router / Tailwind / axios / recharts / vitest; Docker Compose, GitHub, Render static site + web service + PostgreSQL

## Quick Start (Local Dev)

ต้องมี Python 3.11, Node 20, Docker พร้อมเปิด engine

### 1. Postgres

ที่โฟลเดอร์ราก:

```sh
cp .env.example .env
python3.11 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

นำค่าสุ่มไปตั้ง POSTGRES_PASSWORD และส่วน password ใน DATABASE_URL ให้ตรงกัน สุ่มอีกครั้งสำหรับ JWT_SECRET โดยไม่ใช้รหัสผ่านบัญชีบุคคล

```sh
docker compose up -d --wait
```

### 2. Backend

```sh
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs — liveness: /api/v1/healthz — readiness: /api/v1/readyz

### 3. Frontend

เปิด terminal อีกหน้าจากโฟลเดอร์ราก:

```sh
cd frontend
npm ci
npm run dev
```

เปิด http://localhost:5173 โดย Vite proxy /api ไป localhost:8000

## Staff workspace

เปิด `/staff` เพื่อเข้าสู่ระบบเจ้าหน้าที่ ระบบรองรับ:

- เข้าสู่ระบบ ออกจากระบบ ตรวจ session เปลี่ยนรหัส และ reset password ทางอีเมลเมื่อมีค่า `RESEND_API_KEY`/`RESET_EMAIL_FROM`
- แอดมินจัดการผู้ใช้และสิทธิ์หลัก
- Reception ลงทะเบียนคนไข้ ดูคำขอจองจากหน้าเว็บ ยืนยันเป็นคนไข้และนัดหมายจริง
- Practitioner เปิดแฟ้มคนไข้ บันทึก OPD/การตรวจ/แผนดูแล และข้อมูลแพทย์แผนไทย เช่น จักรราศี/ธาตุจากวันเกิด
- งานนัดหมาย หัตถการ คลังยา การจ่ายยา การเงิน ใบรับเงิน คืนเงิน ปิดยอดเงินสด และแนบเอกสารยินยอม

## บัญชีและข้อมูลทดสอบ

ไม่เก็บรหัสผ่านบัญชีจริงใน repository และไม่ seed ข้อมูลคนไข้จริง หากต้องทดสอบ production ให้ใช้ข้อมูลสมมติที่ระบุชัดและลบหลังทดสอบตามนโยบายคลินิก

## โครงสร้างโปรเจกต์

backend/app แยก models, schemas, routers, services, deps, config, database, main; backend/alembic และ scripts; tests แยก unit/integration/acceptance/concurrency

frontend/src แยก pages/components/layouts/api; docs มี requirements, ER, API, architecture, readiness และ evidence; render.yaml ใช้เป็น Blueprint อ้างอิงของ Render

## Branching & Commit convention

main ใช้เป็น branch production ที่ Render deploy; งานแต่ละชิ้นควรใช้ `codex/` prefix เมื่อทำ branch ใหม่; commit ใช้ feat:/fix:/docs:/test:/chore: พร้อมบอกเหตุผล และต้องมีหลักฐานทดสอบก่อน deploy

## Verification

หลังเปิด Postgres และตั้ง .env แล้ว:

```sh
cd backend
source .venv/bin/activate
ruff check .
pytest -v --cov=app --cov-report=term-missing
```

Frontend:

```sh
cd frontend
npm test -- --run
npm run build
```

รอบล่าสุดก่อน deploy `401f9cc`: frontend build ผ่าน, vitest ผ่าน, ruff เฉพาะไฟล์ที่แก้ผ่าน, API import ผ่าน; local acceptance pytest เฉพาะ public booking ยังรันไม่ได้เพราะ PostgreSQL local ที่ตั้งไว้ไม่ตอบสนองในเครื่องนี้ แต่ production API readiness ผ่านหลัง deploy

## Render

Production ใช้ Render static site สำหรับ frontend และ Render web service สำหรับ API โดย frontend ตั้ง `VITE_API_BASE_URL` ไปที่ `https://clinic-api-rl26.onrender.com/api/v1` และ backend ตั้ง CORS ให้รองรับ frontend production

ห้ามใช้ repository เป็นที่เก็บ secret. ค่าเช่น `JWT_SECRET`, `DATABASE_URL`, `RESEND_API_KEY`, `RESET_EMAIL_FROM` ต้องอยู่ใน Render Environment เท่านั้น

## Authentication

Backend และ staff UI รองรับ login/logout/me/change-password/reset-password แล้ว ดูรายละเอียดที่ [วิธีสร้างผู้ดูแลและผลตรวจสิทธิ์](docs/07-auth-step4.md) และ [การรีเซ็ตทางอีเมล](docs/10-password-recovery.md)

## เอกสารสถานะ

- [ตรวจความพร้อมระบบ](docs/12-readiness-check.md)
- [ความคืบหน้าทะเบียน/OPD](docs/09-records-progress.md)
- [รายการหัตถการและบริการ](docs/08-live-services.md)
- [กฎจักรราศี/ธาตุ](docs/06-zodiac-reference.md)
