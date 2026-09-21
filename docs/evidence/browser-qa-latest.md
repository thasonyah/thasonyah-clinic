# Browser QA ล่าสุด — 15 กันยายน 2026

ทดสอบกับระบบสาธิตที่เปิดอยู่บน `127.0.0.1:5174` และ API `127.0.0.1:8001` โดยใช้ข้อมูลสมมติเท่านั้น

## ผ่านแล้ว

- Login บทบาทการเงิน เปิดรายการค่ารักษาที่สร้างใหม่ และบันทึกรับเงินบางส่วนสำเร็จ
- หน้ารายการแสดงสถานะชำระบางส่วน ยอดรับแล้ว และยอดค้างชำระหลังบันทึก
- เปิดรายการเดิมในบทบาทการเงิน และบันทึกคืนเงินบางส่วนจากช่องทางเงินสดสำเร็จ
- หน้ารายการแสดงสถานะคืนเงินบางส่วน และยอดคืนแล้วหลังบันทึก
- Login บทบาทเภสัชกรรม เปิดใบสั่งยาที่สร้างใหม่ และจ่ายยาบางส่วน 2 จาก 5 หน่วยสำเร็จ
- หน้ารายการแสดงสถานะจ่ายบางส่วน และยังเหลือยอดที่ยังไม่จ่าย
- เปิดยอดคงเหลือแยกล็อตจากหน้าเภสัชกรรม และบันทึกตรวจนับล็อตสำเร็จ
- ทวน mobile viewport ของหน้าการเงิน ใบสั่งยา และตรวจนับล็อตแล้ว ไม่มี horizontal overflow
- จำลอง session หมดอายุระหว่างกรอกบันทึก OPD แล้วระบบขึ้นหน้า login เพื่อทำงานต่อ รักษาร่างไว้ในหน่วยความจำ และบันทึกต่อได้หลัง login บัญชีเดิม
- ปิดยอดเงินสดประจำวันผ่านหน้าการเงินสำเร็จ โดยบันทึกยอดนับจริง หมายเหตุ และแสดงสถานะปิดยอดแล้ว
- แสดงเอกสารใบรับเงิน / ใบคืนเงินแบบพิมพ์ได้ แยกตามเลข RCT/RF พร้อมเลข invoice รายการอ้างอิง ช่องทาง ยอดเงิน และช่องลงชื่อ
- แนบเอกสารยินยอมผ่านหน้าทะเบียนคนไข้สำเร็จ รองรับ PDF/JPEG/PNG จำกัด 5 MB และแสดงรายการไฟล์พร้อมดาวน์โหลด
- รอบ pharmacy และ stock adjustment ไม่มี console error ใหม่ ส่วน session-expiry มี 401 console ตามการจำลอง token หมดอายุ

## หลักฐานภาพ

- `docs/design-preview/qa-partial-payment-latest.png`
- `docs/design-preview/qa-partial-refund-latest.png`
- `docs/design-preview/qa-partial-dispense-latest.png`
- `docs/design-preview/qa-stock-adjustment-latest.png`
- `docs/design-preview/qa-billing-mobile-latest.png`
- `docs/design-preview/qa-pharmacy-mobile-latest.png`
- `docs/design-preview/qa-stock-mobile-latest.png`
- `docs/design-preview/qa-session-expired-panel-latest.png`
- `docs/design-preview/qa-session-relogin-save-latest.png`
- `docs/design-preview/qa-cash-close-latest.png`
- `docs/design-preview/qa-official-receipts-latest.png`
- `docs/design-preview/qa-billing-with-official-receipts-latest.png`
- `docs/design-preview/qa-consent-upload-latest.png`

## ขอบเขตที่ยังไม่ได้พิสูจน์ใน browser รอบนี้

- ยังไม่ได้ทดสอบ UAT ครบทุกบทบาทแบบเดินงานทั้งวัน และยังไม่ได้ทดสอบบน deployment จริง
