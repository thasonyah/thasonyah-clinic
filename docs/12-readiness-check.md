# ตรวจความพร้อมระบบ — 27 กันยายน 2026

## ผลรอบล่าสุด

- GitHub repository production ใช้ `https://github.com/thasonyah/thasonyah-clinic` และ Render deploy จาก branch `main`
- Backend API `https://clinic-api-rl26.onrender.com/api/v1` deploy commit `401f9cc` แล้ว และ readiness endpoint ตอบ `{"status":"ready"}`
- Frontend `https://clinic-web-3z3c.onrender.com/` deploy commit `401f9cc` แล้ว โดยหน้า Render ระบุ `Last successfully deployed commit` เป็น commit เดียวกัน
- เพิ่ม flow ให้ Reception ยืนยันคำขอจองจากหน้าเว็บเป็นคนไข้และนัดหมายจริงใน staff scheduling โดยเลือกผู้รักษาและทรัพยากรได้
- Build/verification ล่าสุด: frontend production build ผ่าน, vitest ผ่าน, ruff เฉพาะไฟล์ที่แก้ผ่าน, backend app import ผ่าน
- Local acceptance pytest ของ public booking ยังไม่ได้รันผ่านในเครื่องนี้เพราะ PostgreSQL local ที่ config ไว้ไม่ตอบสนอง; ไม่พบหลักฐานว่าเกิดจากโค้ดใหม่

## ขอบเขตหลักฐาน

การตรวจ production รอบนี้ยืนยันว่า API พร้อมใช้งานและ frontend bundle มีข้อความ/endpoint ของ flow “สร้างนัดจากคำขอ” แล้ว แต่ยังไม่ได้สร้างข้อมูลคนไข้สมมติบน production เพื่อหลีกเลี่ยงการปนข้อมูลทดสอบกับระบบจริง

Browser QA เดิมครอบคลุม flow หลักของการเงินและเภสัชกรรมบน desktop/mobile รวมถึง session หมดอายุระหว่างกรอก ดู `docs/evidence/browser-qa-latest.md` และภาพ `docs/design-preview/qa-*-latest.png` ส่วนผล API tests เดิมไม่แทนการทดสอบหน้าจอครบทุกบทบาทบน production

## สิ่งที่ทำเสร็จแล้วระดับ production

1. Repository และ Render เชื่อมกับบัญชี/โปรเจกต์ที่ผู้ใช้เลือก
2. Public landing page แสดงข้อมูลคลินิกจริง เบอร์โทร LINE ที่อยู่ แผนที่ เวลาเปิด และรายการบริการ
3. Public booking request บันทึกคำขอจอง และ staff สามารถยืนยันเป็น patient + appointment ได้
4. Staff authentication, password reset flow, admin user management, patient records, OPD, scheduling, service catalog, pharmacy, billing, receipts/refunds, cash close และ consent attachment มีโค้ดและหลักฐานทดสอบระดับระบบแล้ว
5. ฟอนต์ FC Vision ถูกใช้เป็นฟอนต์หลัก และแก้ปุ่มพื้นสีทึบให้ตัวอักษรอ่านได้บน production แล้ว

## ยังต้องทำก่อนเปิดใช้งานจริงกับข้อมูลคนไข้จริง

1. ทดสอบ production smoke test ด้วยข้อมูลสมมติหนึ่งชุดในเวลาที่คลินิกยอมรับ แล้วลบ/ทำเครื่องหมายข้อมูลทดสอบหลังตรวจครบ flow
2. ตรวจรับกฎจันทรคติ/จักรราศีในเคสอธิกมาสและอธิกวารเพิ่มเติมกับผู้เชี่ยวชาญ ก่อนใช้ผลอัตโนมัติเป็นข้อมูลประกอบเวชระเบียนจริง
3. ตั้งและทดสอบนโยบาย backup/restore บน Render production database ตามรอบที่คลินิกต้องการ
4. ทดสอบส่ง reset email จริงจาก domain/อีเมลที่ตั้งค่าไว้ และตรวจ spam/deliverability
5. ตรวจทานและอนุมัติคู่มือใช้งานรายบทบาทใน `docs/13-user-guide.md` กับเจ้าหน้าที่จริง
6. กำหนดนโยบายสิทธิ์ใช้งานจริงของคลินิก เช่น ใครเป็นแอดมิน ผู้รักษา reception และสิทธิ์ดูข้อมูลคนไข้ข้ามเคส

ระบบพร้อมสำหรับการตรวจรับรอบ production smoke test แต่ยังไม่ควรเปิดรับข้อมูลคนไข้จริงจนกว่าจะปิดรายการข้างต้น
