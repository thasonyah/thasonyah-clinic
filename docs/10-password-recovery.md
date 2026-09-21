# บัญชีผู้ดูแลและการรีเซ็ตทางอีเมล

13 กันยายน 2569

ผู้ใช้ยืนยัน thasonyahclinic@gmail.com เป็นบัญชีผู้ดูแลคลินิก สร้างในฐาน local แล้ว (ไม่ใช่ production) รหัสเริ่มต้นสุ่มใหม่ เก็บ bcrypt ในฐานข้อมูลและส่งมอบผ่านไฟล์ส่วนตัวนอก repository ไม่บันทึกรหัสผ่านในเอกสารนี้

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

ตั้งใน .env หรือ Render environment เท่านั้น:

- RESEND_API_KEY — key สำหรับส่งอีเมล
- RESET_EMAIL_FROM — อีเมลจากโดเมนผู้ส่งที่ยืนยันแล้ว
- RESET_PUBLIC_URL — HTTPS URL ของ frontend เช่น https://clinic.example/staff ไม่มี query/fragment

HTTP adapter ใช้ Resend โดยยังไม่มีการเปิดบัญชีหรือส่งอีเมลจริง เอกสาร API: https://resend.com/docs/api-reference/emails/send-email
สามารถเปลี่ยน adapter หากคลินิกมีผู้ให้บริการเดิม โดยไม่เปลี่ยน flow หรือฐานข้อมูล

ต้องใส่สามค่านี้และทดสอบรับเมลจริงก่อนถือว่าการส่งอีเมลพร้อมใช้งาน Background task ปัจจุบันไม่ใช่ durable mail queue หาก worker หยุดระหว่างส่งให้ขอลิงก์ใหม่ ไม่มีการอ้างว่าส่งสำเร็จแน่นอนจากเพียงการรับคำขอ

## หลักฐาน

pytest รวม 12 tests ผ่าน 94% ของโค้ดปัจจุบัน (ไม่ใช่ coverage ทั้งโครงการ)
ทดสอบ single use, session revoke, รหัสเก่าเข้าไม่ได้/ใหม่เข้าได้, expired/invalid token, missing email config และสองคำขอพร้อมกันสำเร็จหนึ่งครั้ง โดย mock ผู้ส่งเพื่อไม่ส่งเมลจริง
Build frontend ผ่าน; ไม่มีการกรอกรหัสผ่านใหม่ของผู้ใช้ผ่านเครื่องมือ browser
