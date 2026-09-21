# ระบบคลินิกแพทย์แผนไทย

โครงโปรเจกต์ขั้นที่ 3 ยังไม่มีระบบเข้าสู่ระบบหรือฟีเจอร์คนไข้ ชื่อ repository รอเจ้าของยืนยัน

## Live Deployment

ยังไม่ได้ deploy จึงยังไม่มี URL frontend หรือ API docs จริง ไฟล์ render.yaml เป็น Blueprint สำหรับ demo ให้ตรวจชื่อ resource, Singapore region และแผนบริการก่อนสร้าง ห้ามใช้ demo เป็นที่เก็บข้อมูลคนไข้จริง

## Tech Stack

Python 3.11 / FastAPI / SQLAlchemy 2 / Alembic / Pydantic v2 / PostgreSQL 15 / python-jose / passlib / bcrypt 4.0.1 / slowapi / pytest / httpx / pytest-cov / ruff

React 18 / Vite 5 / Router / Tailwind 3 / axios / recharts / vitest; Docker Compose, GitHub Actions และ Render

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

## บัญชีทดลอง

ยังไม่มีบัญชีทดลองและ seed ยังไม่สร้างข้อมูล ขั้นที่ 6 จะเพิ่มข้อมูลสมมติ พร้อมข้อความ “บัญชีทดลอง เปิดเผยโดยเจตนา ไม่มีข้อมูลจริง” ห้ามนำบัญชีส่วนบุคคลมาเป็น seed

## โครงสร้างโปรเจกต์

backend/app แยก models, schemas, routers, services, deps, config, database, main; backend/alembic และ scripts; tests แยก unit/integration/acceptance/concurrency

frontend/src แยก pages/components/layouts/api; docs มี requirements, ER, API และ architecture; .github/workflows/ci.yml, docker-compose.yml, render.yaml

## Branching & Commit convention

main รับเฉพาะ PR ที่ผ่าน backend-test และ frontend-build; งานแต่ละชิ้นใช้ codex/ prefix; commit ใช้ feat:/fix:/docs:/test:/chore: พร้อมบอกเหตุผล; PR มีหัวข้อ “พิสูจน์ยังไงว่าถูก”; squash merge แล้วลบ branch

## Verification

หลังเปิด Postgres และตั้ง .env แล้ว:

```sh
cd backend
source .venv/bin/activate
ruff check .
pytest -v --cov=app --cov-report=term-missing
```

Frontend: npm test และ npm run build ใน frontend (scaffold ยังไม่มี frontend test cases)

## Render

Blueprint สร้าง DB + backend + static frontend; กรอก CORS_ORIGINS เป็น JSON array ของ URL frontend และ VITE_API_BASE_URL เป็น https://<backend-host>/api/v1 จาก URL จริงของ Render แล้ว rebuild frontend; JWT_SECRET สร้างโดย Render; PostgreSQL 15 และ Python 3.11.9 ถูกตรึงไว้

Migration baseline ว่าง ฟีเจอร์จะเพิ่มตารางผ่าน Alembic ทีละ PR ใช้ PostgreSQL ทั้ง dev/CI ห้าม SQLite

## Authentication (ขั้น 4)

Backend รองรับ login/logout/me/change-password และ admin list/create users แล้ว
ดู [วิธีสร้างผู้ดูแลและผลตรวจสิทธิ์](docs/07-auth-step4.md)
ยังไม่มีบัญชีทดลองหรือหน้าล็อกอินจริง; `/design/*` เป็นหน้าต้นแบบและไม่ใช่พื้นที่เก็บข้อมูลคนไข้จริง
