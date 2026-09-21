# ขั้นที่ 2 — REST API specification v1

สถานะ: design contract สำหรับ P1; endpoints ระยะถัดไปเป็น resource map ยังไม่ใช่ API ที่เปิดใช้งาน Base path /api/v1 ใช้ JSON; UUID ใน path; timestamp RFC3339; วัน YYYY-MM-DD เป็น ค.ศ. ฝั่ง UI แปลง พ.ศ. อย่างชัดเจน; amount/quantity ส่ง decimal string; ปฏิเสธ unknown fields ใน write schemas

## สัญญาร่วม

- Authorization: Bearer access token สำหรับ protected endpoints ตรวจ session และ user active ผ่าน deps.py ทุกครั้ง
- ทุก list ใช้ limit (default 25, max 100), cursor และ filters ที่ allowlist; response {items,next_cursor}; ไม่ส่ง binary/clinical body ใน list ที่ไม่จำเป็น
- Error: {error:{code,message,fields},request_id}; ไม่มี stacktrace/SQL/PII
- 200 read/update/replay; 201 create; 204 logout; 401 invalid identity; 403 missing action permission; 404 resource นอกขอบเขต/ไม่พบ; 409 state/version/resource/idempotency conflict; 422 validation; 429 rate limit
- mutation ที่มี version ส่ง expected_version; replay สำเร็จใช้ status/body เดิม; financial/booking/dispensing endpoints บังคับ Idempotency-Key
- client ไม่เลือกผู้บันทึก/ผู้อนุมัติแทน identity; patient/branch access ตรวจทุก FK ใน body ไม่ใช่เฉพาะ URL
- allowed public: POST auth/login และ GET healthz; ผ่าน public dependency; readiness GET readyz คืนเพียงสถานะพร้อมหรือ 503 ไม่เผย connection

## Identity และการตั้งค่า

| Method / path | สิทธิ์ | Request → Response |
|---|---|---|
| POST /auth/login | public + rate limit | email,password → access_token,token_type,expires_in,user_summary; ใช้ generic failure |
| POST /auth/logout | authenticated | ไม่มี body → 204 และ revoke session |
| GET /auth/me | authenticated | → user,permissions,allowed_branches ไม่มี password hash |
| GET, POST /users | users.manage | list / email,role_ids,branch_ids → user; รหัสเริ่มต้นรับผ่านช่องทางเฉพาะ ไม่ส่งคืน hash |
| PATCH /users/{id} | users.manage | active,role_ids,branch_ids,expected_version → user; ป้องกันถอดสิทธิ์ผู้ดูแลคนสุดท้าย |
| POST /auth/change-password | authenticated | current_password,new_password → result; revoke sessions อื่น |
| GET, POST /branches | clinic.manage | code,name,timezone → branch |
| GET, POST /services | clinic.read / clinic.manage | name,duration,buffer,price,resource_requirements → service |
| PATCH /services/{id} | clinic.manage | editable fields,expected_version → service |
| GET, POST /resources | scheduling.read / clinic.manage | type,parent_id,branch_id,provider_id nullable → resource |
| POST /resources/{id}/blocks | resources.manage | start,end,reason → block; 409 เมื่อชน booking |
| GET /availability | scheduling.read | branch,service,from,to → candidate intervals; เป็นข้อมูลประกอบ ไม่ใช่หลักฐานจองสำเร็จ |

## ทะเบียน นัดหมายและคิว

| Method / path | สิทธิ์ | Request → Response |
|---|---|---|
| GET /patients | patients.read | q,cursor → รายการ minimal identity ตามสิทธิ์ |
| POST /patients | patients.create | name,contact,birth_date,birth_date_precision,contacts → patient + zodiac status |
| GET /patients/{id} | patients.read + scope | → demographics; ไม่แนบเวชระเบียนโดยปริยาย |
| PATCH /patients/{id} | patients.update + scope | changed fields,expected_version → patient; วันเกิดเปลี่ยนสร้าง zodiac snapshot ใหม่ |
| GET, POST /patients/{id}/health-profiles | clinical.read / clinical.write + scope | history,allergy_status,allergies,current_medications → versioned profile |
| GET /patients/{id}/zodiac | clinical.read + scope | → calculation_status,reason,input_date,ruleset_version,result; ไม่มี diagnosis |
| GET /patients/{id}/visits | clinical.read + scope | → visit summaries ที่มีสิทธิ์ |
| GET, POST /appointments | scheduling.read / scheduling.write | POST patient_id,branch_id,service_id,resource_ids,start_at → confirmed appointment; idem required |
| POST /appointments/{id}/reschedule | scheduling.write + scope | new_start,resource_ids,expected_version → updated appointment; idem required |
| POST /appointments/{id}/cancel | scheduling.write + scope | reason,expected_version → cancelled; idem required |
| POST /visits | queues.write | patient_id,branch_id,appointment_id nullable → waiting visit; idem required |
| GET /queues | queues.read | branch,state → queues ตามข้อมูลจำเป็น |
| POST /visits/{id}/transitions | queues.write + scope | target_state,expected_version → visit; role อาจเปลี่ยนตาม transition |

ตัวอย่างจอง POST /appointments พร้อม Idempotency-Key ที่ไม่ซ้ำ:

```json
{"patient_id":"<uuid>","branch_id":"<uuid>","service_id":"<uuid>","resource_ids":["<provider-resource-uuid>","<bed-resource-uuid>"],"start_at":"2026-10-01T09:00:00+07:00"}
```

Server คำนวณ end จากบริการและตรวจ requirements เอง ไม่เชื่อจำนวนเงิน/เวลาสิ้นสุดจาก client หากช่องถูกจองคืน 409 SLOT_UNAVAILABLE และไม่มี resource ถูกยึดค้าง

## ตรวจและรักษา

| Method / path | สิทธิ์ | Request → Response |
|---|---|---|
| GET /visits/{id} | clinical.read + assignment | → visit, revision summaries, observations, zodiac_snapshot |
| POST /visits/{id}/clinical-revisions | clinical.write + assignment | form_version_id,payload,source_revision_id nullable → draft revision |
| PATCH /clinical-revisions/{id} | clinical.write + assignment | payload,expected_version → draft; signed คืน 409 |
| POST /clinical-revisions/{id}/sign | clinical.sign + assignment | expected_version → immutable signed revision |
| POST /clinical-revisions/{id}/amendments | clinical.sign + assignment | reason,payload → new draft linked to original |
| POST /visits/{id}/observations | clinical.write + assignment | instrument_code,version,value,unit,measured_at → observation |
| POST /visits/{id}/body-marks | clinical.write + assignment | diagram_version,x,y,side,description → mark |
| POST /visits/{id}/diagnoses | clinical.sign + assignment | text,status,evidence,reference → diagnosis |
| POST /visits/{id}/treatment-plans | clinical.sign + assignment | goals,services,review_date,stop_conditions → plan |
| POST /visits/{id}/procedures | clinical.perform + assignment | service_id,site,start,end,technique,before,after → procedure; provider จาก token |
| GET, POST /visits/{id}/followups | clinical.read / clinical.write | due_at,owner,goals → followup |
| POST /visits/{id}/referrals | clinical.sign | reason,destination,documents → referral |
| POST /visits/{id}/adverse-events | clinical.write | event,occurred_at,owner,actions → event |
| GET, POST /visits/{id}/consents | documents.read / documents.write + scope | template_version,signer,evidence_attachment → consent |

Form payload แยก subjective, examination, element_assessment, samutthana_assessment, assessment_reasoning; zodiac_snapshot เป็น read-only reference จากระบบ ไม่อนุญาต frontend ตั้งผลคำนวณเอง

## ยาและคลัง

| Method / path | สิทธิ์ | Request → Response |
|---|---|---|
| GET, POST /products | inventory.read / inventory.manage | code,name,base_unit,type → product |
| GET /stock-balances | inventory.read | branch,product,expiry_before → balances |
| POST /stock-receipts | inventory.receive | branch,product,batch,expiry,quantity,unit → lot/balance/movement; idem required |
| POST /stock-adjustments | inventory.adjust | balance,delta,reason,approval_id → movement; idem required |
| POST /stock-lots/{id}/hold | inventory.hold | reason,expected_version → held lot |
| POST /visits/{id}/prescriptions | prescriptions.write + assignment | items(product,dose,route,frequency,duration,instructions,quantity,unit) → draft |
| POST /prescriptions/{id}/sign | prescriptions.sign + assignment | expected_version → signed prescription |
| POST /dispenses | dispensing.write + scope | prescription_id,items(prescription_item_id,lot_id,quantity),expected_version → dispense; idem required |
| POST /dispenses/{id}/returns | dispensing.return | items,reason → quarantined return + movements; idem required |

ตัวอย่าง dispense: ถ้า lot จ่ายได้แต่จำนวนเกินคำสั่งที่เหลือ rollback ทั้ง stock และ order balance; partial fulfillment คือผู้ใช้ระบุจำนวนบางส่วนสำเร็จ ไม่ใช่ transaction สำเร็จบางรายการโดยไม่แจ้ง

## การเงิน เอกสารและตรวจสอบ

| Method / path | สิทธิ์ | Request → Response |
|---|---|---|
| POST /invoices | billing.write | visit_id,items(source_id,quantity),discount_request nullable → draft invoice; ราคาคำนวณฝั่ง server |
| POST /invoices/{id}/issue | billing.issue | expected_version → issued invoice |
| POST /payments | billing.collect | patient_id,branch_id,amount,channel,allocations,deposit_amount → payment/receipt; idem required |
| POST /refunds | billing.refund + approval | payment_id,amount,reason,approval_id → refund/reversal; idem required |
| POST /invoices/{id}/void | billing.void + approval | reason,expected_version,approval_id → void document; ไม่ลบ payment |
| GET /receipts/{id} | billing.read + scope | → receipt; export ตรวจสิทธิ์เช่นกัน |
| POST /cash-sessions | billing.close | branch_id → session |
| POST /cash-sessions/{id}/close | billing.close | counted_by_channel,reason,expected_version → reconciliation |
| GET, POST /approvals | approvals.read / approvals.request | action,target_id,target_version,reason → pending request |
| POST /approvals/{id}/decision | permission ของ action ที่อนุมัติ | decision,reason,expected_version → decision; ไม่อนุมัติตัวเองถ้านโยบายบังคับแยก |
| GET /reports/daily-finance | reports.finance + branch | from,to,branch → sales,receipts,deposits,refunds,outstanding พร้อม definition |
| GET /reports/clinic-activity | reports.operations + branch | from,to,branch → visits,no_shows,wait_times |
| POST /attachments | documents.write + owner scope | multipart file,owner_type,owner_id → metadata; validate MIME/size |
| GET /attachments/{id}/download | documents.read + owner scope | → authenticated binary attachment; no public URL |
| GET /audit-events | audit.read + scope | target,actor,from,to → redacted events |
| GET /healthz, /readyz | explicit public dependency | → minimal status; readyz 503 ถ้า DB ไม่พร้อม |

## Resource map P2–P4

| FR | API families |
|---|---|
| 04,29 | /patient-merges, /import-jobs, /privacy-requests |
| 16,17 | /suppliers, /purchase-orders, /goods-receipts, /recalls, /formula-versions, /production-batches |
| 20 | /package-versions, /patient-packages, /package-redemptions, /package-reversals |
| 21,22 | /portal/me, /portal/appointments, /waitlist, /notification-preferences, /deliveries |
| 23,24 | /form-templates, /remote-consents, /tasks, /surveys, /complaints, /campaigns |
| 25–28 | /rosters, /leave-requests, /credentials, /compensation, /expenses, /payables, /stock-transfers, /maintenance |
| 31–33 | /integrations, /webhooks/{provider}, /knowledge, /ai-drafts, /claims, /lab-orders |

Webhook ไม่ใช้ staff JWT แต่ต้องใช้ provider signature, timestamp/replay checks และ unique event_id; คืนสำเร็จหลังบันทึกรับ event ทนทาน ไม่ถือว่า payment สำเร็จจาก redirect หน้าเว็บ

## Verification / RTM

ทุก FR ใน 01-requirements.md อ้างโมดูลใน 02-architecture.md; API P1 ข้างต้นต้องมี schema และ tests ก่อน merge implementation ส่วน P2–P4 ต้องแตก request/response ตาม provider และกฎจริงก่อนเริ่มแต่ละเฟส ไม่ถือ resource map ว่าเป็นสัญญาปลายทางสมบูรณ์

ชุดทดสอบ P1: auth 401/403, cross-branch/object 404, concurrent booking/last stock 10 threads, repeated payment/refund, partial dispense rollback, optimistic conflict, signed revision protection, zodiac boundary fixtures, report reconciliation, attachment permission, DB migration และ restore rehearsal
