# บัญชีผู้ดูแลและการรีเซ็ตทางอีเมล

22 กันยายน 2569

ผู้ใช้ยืนยัน thasonyahclinic@gmail.com เป็นบัญชีผู้ดูแลคลินิก รหัสผ่านเก็บแบบ bcrypt ในฐานข้อมูล ไม่บันทึกรหัสผ่านหรือ API key ในเอกสารนี้

## ฟังก์ชัน

- ลืมรหัสผ่านจากหน้า /staff: POST /auth/forgot-password
- ลิงก์ /staff#reset=<token> อายุ 15 นาที ใช้ได้ครั้งเดียว; frontend เอา fragment ออกจาก address bar หลังอ่านเข้า memory
- POST /auth/reset-password: รหัสใหม่อย่างน้อย 12 ตัวอักษร ไม่เกิน 72 UTF-8 bytes
- เก็บเฉพาะ SHA-256 ของ token ใน PostgreSQL; ไม่คืน token ใน API หรือ log
- เมื่อสำเร็จ revoke ทุก session และใช้ reset tokens อื่นทั้งหมดไม่ได้
- คำตอบขอรีเซ็ตเหมือนกันทั้งอีเมลที่มี/ไม่มีบัญชี; บัญชี inactive ไม่ส่ง
- Rate limit 5/minute ต่อ IP; ส่งผ่าน background task
- ถ้าไม่ตั้งค่าผู้ส่ง คืน 503 พร้อมแจ้งว่าระบบอีเมลยังไม่พร้อม ไม่อ้างว่าส่งแล้ว

## ตั้งค่าการส่งจริง

ตั้งใน `.env` ตอนพัฒนา หรือ Render Environment ของ service `clinic-api` เท่านั้น:

- RESEND_API_KEY — key สำหรับส่งอีเมล
- RESET_EMAIL_FROM — อีเมลจากโดเมนผู้ส่งที่ยืนยันแล้ว
- RESET_PUBLIC_URL — HTTPS URL ของ frontend เช่น https://clinic-web-3z3c.onrender.com/staff ไม่มี query/fragment


สำหรับ production บน Render ชุดนี้ต้องอยู่ที่ `clinic-api`:

```text
RESEND_API_KEY=<Resend API key>
RESET_EMAIL_FROM=onboarding@resend.dev  # ใช้ชั่วคราวจนกว่าจะ verify domain ของคลินิกใน Resend
RESET_PUBLIC_URL=https://clinic-web-3z3c.onrender.com/staff
```

ไม่ต้องใส่สามค่านี้ใน `clinic-web` เพราะ frontend เรียก API และ API เป็นผู้ส่งอีเมลจริง

สถานะ production ล่าสุด: `clinic-api` ตั้งค่า Resend แล้ว ทดสอบ `/api/v1/auth/forgot-password` ได้ `202 Accepted` และ log ไม่มี `Password reset email delivery failed` หลังเปลี่ยน `RESET_EMAIL_FROM` เป็น `onboarding@resend.dev`

Resend ไม่อนุญาตให้ใช้ `thasonyahclinic@gmail.com` เป็นผู้ส่งโดยตรง เพราะโดเมน `gmail.com` ไม่ได้ verify กับบัญชีนี้ หากต้องการผู้ส่งถาวรของคลินิกให้เพิ่มและยืนยันโดเมนใน Resend ก่อน แล้วค่อยเปลี่ยนเป็นเช่น `noreply@โดเมนคลินิก` หรือ `contact@โดเมนคลินิก`

HTTP adapter ใช้ Resend เอกสาร API: https://resend.com/docs/api-reference/emails/send-email
สามารถเปลี่ยน adapter หากคลินิกมีผู้ให้บริการเดิม โดยไม่เปลี่ยน flow หรือฐานข้อมูล

ต้องใส่สามค่านี้และทดสอบรับเมลจริงก่อนถือว่าการส่งอีเมลพร้อมใช้งานเต็มรูปแบบ Background task ปัจจุบันไม่ใช่ durable mail queue หาก worker หยุดระหว่างส่งให้ขอลิงก์ใหม่ ไม่มีการอ้างว่าส่งสำเร็จแน่นอนจากเพียงการรับคำขอ

## หลักฐาน

pytest รวม 12 tests ผ่าน 94% ของโค้ดชุด password reset ตอนพัฒนา (ไม่ใช่ coverage ทั้งโครงการ)
ทดสอบ single use, session revoke, รหัสเก่าเข้าไม่ได้/ใหม่เข้าได้, expired/invalid token, missing email config และสองคำขอพร้อมกันสำเร็จหนึ่งครั้ง โดย mock ผู้ส่งเพื่อไม่ส่งเมลจริง
Production smoke test วันที่ 22 กันยายน 2569: `https://clinic-api-rl26.onrender.com/api/v1/readyz` ได้ 200, `POST /api/v1/auth/forgot-password` สำหรับบัญชีผู้ดูแลได้ 202, log ไม่มี delivery failure หลังใช้ sender `onboarding@resend.dev`
Build frontend ผ่าน; ไม่มีการกรอกรหัสผ่านใหม่ของผู้ใช้ผ่านเครื่องมือ browser
